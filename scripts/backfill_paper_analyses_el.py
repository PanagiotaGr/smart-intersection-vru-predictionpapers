#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from openai import OpenAI

from summarize_papers_el import (
    IMPTC_PROFILE,
    call_llm,
    read_json,
    safe_filename,
    write_json,
)

SCHEMA_VERSION = 3
REQUIRED_FIELDS = {
    "short_summary_el",
    "research_question",
    "authors_work_and_objective",
    "what_problem_does_it_solve",
    "main_method",
    "methodology_detailed",
    "model_architecture_or_algorithm",
    "input_output",
    "datasets_or_scenarios",
    "datasets_vru_types_scenarios",
    "sensors_and_context",
    "evaluation_protocol",
    "metrics",
    "baselines",
    "key_results",
    "evaluation_and_key_results",
    "scientific_contribution",
    "limitations",
    "future_work_authors",
    "future_extensions_for_imptc",
    "why_it_matters_for_thesis",
    "imptc_applicability",
    "imptc_required_adaptations",
    "imptc_relevance_dimensions",
    "imptc_relevance_score",
    "imptc_relevance_label",
    "general_relevance_score",
    "general_relevance_label",
    "evidence_level",
    "keywords_el",
}


def valid_papers(db: Dict[str, Any]) -> List[Dict[str, Any]]:
    papers = []
    for paper in (db.get("papers") or {}).values():
        if paper.get("arxiv_id") and paper.get("title") and paper.get("summary"):
            papers.append(paper)
    papers.sort(key=lambda p: (p.get("published_utc", ""), p.get("arxiv_id", "")))
    return papers


def stale_reasons(record: Any) -> List[str]:
    if not isinstance(record, dict):
        return ["missing_analysis"]
    reasons: List[str] = []
    if int(record.get("schema_version", 0) or 0) < SCHEMA_VERSION:
        reasons.append("old_schema")
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        reasons.append("missing_fields:" + ",".join(missing))
    dimensions = record.get("imptc_relevance_dimensions")
    if not isinstance(dimensions, dict) or len(dimensions) < 8:
        reasons.append("incomplete_imptc_dimensions")
    if record.get("analysis_source") not in {"title_and_abstract", "full_text"}:
        reasons.append("unknown_evidence_source")
    return reasons


def select_batch(
    papers: List[Dict[str, Any]], analyses: Dict[str, Any], limit: int
) -> Tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
    reasons: Dict[str, List[str]] = {}
    candidates: List[Dict[str, Any]] = []
    for paper in papers:
        paper_id = paper["arxiv_id"]
        paper_reasons = stale_reasons(analyses.get(paper_id))
        if paper_reasons:
            reasons[paper_id] = paper_reasons
            candidates.append(paper)
    return candidates[:limit], reasons


def build_record(paper: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "arxiv_id": paper["arxiv_id"],
        "title": str(paper.get("title", "")).strip(),
        "authors": paper.get("authors") or [],
        "published_utc": paper.get("published_utc", ""),
        "updated_utc": paper.get("updated_utc", ""),
        "primary_category": paper.get("primary_category", ""),
        "categories": paper.get("categories") or [],
        "abs_url": paper.get("abs_url", ""),
        "pdf_url": paper.get("pdf_url", ""),
        "source_abstract": str(paper.get("summary", "")).strip(),
        "analysis_source": "title_and_abstract",
        "analysis_language": "el",
        "thesis_dataset": "IMPTC",
        "backfilled_at_utc": datetime.now(timezone.utc).isoformat(),
        **result,
    }


def coverage_report(
    papers: List[Dict[str, Any]], analyses: Dict[str, Any], errors: List[Dict[str, str]]
) -> Dict[str, Any]:
    complete = 0
    stale = 0
    missing = 0
    reason_counts: Dict[str, int] = {}
    for paper in papers:
        record = analyses.get(paper["arxiv_id"])
        reasons = stale_reasons(record)
        if not reasons:
            complete += 1
            continue
        stale += 1
        if "missing_analysis" in reasons:
            missing += 1
        for reason in reasons:
            key = reason.split(":", 1)[0]
            reason_counts[key] = reason_counts.get(key, 0) + 1
    total = len(papers)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema_version": SCHEMA_VERSION,
        "total_source_papers": total,
        "complete_analyses": complete,
        "remaining_stale_or_missing": stale,
        "missing_analyses": missing,
        "coverage_percent": round((complete / total * 100), 2) if total else 100.0,
        "stale_reason_counts": reason_counts,
        "errors_this_run": errors,
        "policy": "oldest-first; all historical papers are upgraded before repeated refreshes",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Αναδρομική ελληνική ανάλυση όλων των παλιών papers, από το παλαιότερο προς το νεότερο."
    )
    parser.add_argument("--db", default="data/papers.json")
    parser.add_argument("--out", default="data/paper_analyses_el.json")
    parser.add_argument("--legacy-out", default="data/paper_summaries_el.json")
    parser.add_argument("--paper-dir", default="data/papers_el")
    parser.add_argument("--report", default="data/backfill_status_el.json")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=0.5)
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    db = read_json(Path(args.db), {"papers": {}})
    existing = read_json(Path(args.out), {"analyses": {}})
    analyses: Dict[str, Any] = existing.get("analyses", {})
    legacy = read_json(Path(args.legacy_out), {"summaries": {}})
    for paper_id, summary in (legacy.get("summaries") or {}).items():
        analyses.setdefault(paper_id, summary)

    papers = valid_papers(db)
    batch, all_reasons = select_batch(papers, analyses, max(args.limit, 0))
    print(f"Historical papers: {len(papers)}; stale/missing: {len(all_reasons)}; batch: {len(batch)}")

    client = OpenAI(api_key=api_key)
    errors: List[Dict[str, str]] = []
    for paper in batch:
        paper_id = paper["arxiv_id"]
        try:
            result = call_llm(
                client,
                args.model,
                str(paper.get("title", "")).strip(),
                str(paper.get("summary", "")).strip(),
                paper.get("authors") or [],
            )
            record = build_record(paper, result)
            analyses[paper_id] = record
            write_json(Path(args.paper_dir) / f"{safe_filename(paper_id)}.json", record)
            write_json(
                Path(args.out),
                {
                    "schema_version": SCHEMA_VERSION,
                    "imptc_profile": IMPTC_PROFILE,
                    "analyses": analyses,
                },
            )
            print(f"[BACKFILLED] {paper_id} :: {paper.get('title', '')}")
            time.sleep(args.sleep)
        except Exception as exc:
            errors.append({"arxiv_id": paper_id, "error": str(exc)})
            print(f"[ERROR] {paper_id} :: {exc}")

    write_json(
        Path(args.out),
        {
            "schema_version": SCHEMA_VERSION,
            "imptc_profile": IMPTC_PROFILE,
            "analyses": analyses,
        },
    )
    report = coverage_report(papers, analyses, errors)
    write_json(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
