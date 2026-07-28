#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "paper"


def claim_id(paper_id: str, claim_type: str, text: str, page: Any) -> str:
    raw = f"{paper_id}|{claim_type}|{page}|{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def normalize_claim(paper_id: str, claim: Dict[str, Any]) -> Dict[str, Any]:
    text = str(claim.get("claim_text_el") or "").strip()
    normalized = {
        "claim_id": claim.get("claim_id") or claim_id(paper_id, str(claim.get("claim_type", "unknown")), text, claim.get("page")),
        "paper_id": paper_id,
        "claim_type": claim.get("claim_type", "unknown"),
        "claim_text_el": text,
        "source_kind": claim.get("source_kind", "body"),
        "page": claim.get("page"),
        "section": claim.get("section"),
        "table": claim.get("table"),
        "figure": claim.get("figure"),
        "quote_or_paraphrase": claim.get("quote_or_paraphrase", "paraphrase"),
        "confidence": claim.get("confidence", "low"),
        "author_claim": bool(claim.get("author_claim", True)),
        "thesis_inference": bool(claim.get("thesis_inference", False)),
        "extraction_method": claim.get("extraction_method", "unknown"),
    }
    if normalized["author_claim"] and normalized["thesis_inference"]:
        raise ValueError("A claim cannot be both author_claim and thesis_inference")
    return normalized


def validate_claim(claim: Dict[str, Any], required: Iterable[str]) -> List[str]:
    errors: List[str] = []
    for key in required:
        if key not in claim:
            errors.append(f"missing:{key}")
    if claim.get("claim_type") == "result" and not claim.get("page"):
        errors.append("result_without_page")
    if claim.get("claim_type") == "result" and not (claim.get("table") or claim.get("figure") or claim.get("section")):
        errors.append("result_without_table_figure_or_section")
    if not claim.get("claim_text_el"):
        errors.append("empty_claim")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Build validated, provenance-aware full-text research records")
    ap.add_argument("--papers", default="data/papers.json")
    ap.add_argument("--extractions", default="data/fulltext_extractions")
    ap.add_argument("--schema", default="config/fulltext_claim_schema.json")
    ap.add_argument("--out", default="data/fulltext_research_records.json")
    ap.add_argument("--paper-dir", default="data/fulltext_records")
    ap.add_argument("--report", default="thesis/quality/fulltext_provenance_report.json")
    args = ap.parse_args()

    papers_db = read_json(Path(args.papers), {"papers": {}})
    papers = papers_db.get("papers") or {}
    schema = read_json(Path(args.schema), {})
    required = schema.get("required_claim_fields") or []
    extraction_dir = Path(args.extractions)
    records: Dict[str, Any] = {}
    report_rows: List[Dict[str, Any]] = []

    for paper_id, paper in sorted(papers.items()):
        source = extraction_dir / f"{safe_name(paper_id)}.json"
        payload = read_json(source, {})
        raw_claims = payload.get("claims") or []
        claims: List[Dict[str, Any]] = []
        validation_errors: List[Dict[str, Any]] = []
        for raw in raw_claims:
            try:
                claim = normalize_claim(paper_id, raw)
                errors = validate_claim(claim, required)
                if errors:
                    validation_errors.append({"claim_id": claim["claim_id"], "errors": errors})
                claims.append(claim)
            except Exception as exc:
                validation_errors.append({"claim_id": raw.get("claim_id"), "errors": [str(exc)]})

        valid_count = len(claims) - len(validation_errors)
        evidence_level = payload.get("evidence_level") or ("full_text" if claims else "title_and_abstract")
        record = {
            "schema_version": 1,
            "paper_id": paper_id,
            "title": paper.get("title", ""),
            "pdf_url": paper.get("pdf_url", ""),
            "evidence_level": evidence_level,
            "source_file": str(source) if source.exists() else None,
            "claims": claims,
            "validation_errors": validation_errors,
            "provenance_coverage": round(valid_count / len(claims) * 100, 2) if claims else 0.0,
            "eligible_for_numerical_synthesis": bool(claims) and not any(
                "result_without" in err for row in validation_errors for err in row.get("errors", [])
            ),
        }
        records[paper_id] = record
        write_json(Path(args.paper_dir) / f"{safe_name(paper_id)}.json", record)
        report_rows.append({
            "paper_id": paper_id,
            "evidence_level": evidence_level,
            "claim_count": len(claims),
            "validation_error_count": len(validation_errors),
            "provenance_coverage": record["provenance_coverage"],
            "eligible_for_numerical_synthesis": record["eligible_for_numerical_synthesis"],
        })

    write_json(Path(args.out), {"schema_version": 1, "records": records})
    write_json(Path(args.report), {
        "schema_version": 1,
        "total_papers": len(records),
        "papers_with_fulltext_claims": sum(1 for r in report_rows if r["claim_count"] > 0),
        "papers_eligible_for_numerical_synthesis": sum(1 for r in report_rows if r["eligible_for_numerical_synthesis"]),
        "papers": report_rows,
    })
    print(f"Built {len(records)} provenance-aware research records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
