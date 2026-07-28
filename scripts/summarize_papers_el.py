#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def build_prompt(title: str, abstract: str, authors: List[str]) -> str:
    return f"""
Ανάλυσε επιστημονικά το παρακάτω paper στα ελληνικά, χρησιμοποιώντας αποκλειστικά όσα τεκμηριώνονται από τον τίτλο και το abstract.

Τίτλος: {title}
Συγγραφείς: {', '.join(authors)}
Abstract: {abstract}

Επέστρεψε ΜΟΝΟ έγκυρο JSON με ακριβώς αυτά τα πεδία:
{{
  "short_summary_el": "...",
  "research_question": "...",
  "authors_work_and_objective": "...",
  "what_problem_does_it_solve": "...",
  "main_method": "...",
  "methodology_detailed": "...",
  "input_output": "...",
  "datasets_or_scenarios": "...",
  "datasets_vru_types_scenarios": "...",
  "key_results": "...",
  "evaluation_and_key_results": "...",
  "scientific_contribution": "...",
  "limitations": "...",
  "future_work": "...",
  "why_it_matters_for_thesis": "...",
  "relevance_score": 0,
  "relevance_label": "...",
  "keywords_el": ["...", "...", "..."]
}}

Κανόνες:
- Όλο το κείμενο να είναι στα ελληνικά, με ακαδημαϊκό και σαφή λόγο.
- Μην επινοείς datasets, metrics, αποτελέσματα, αρχιτεκτονικές, περιορισμούς ή future work.
- Όταν κάτι δεν δηλώνεται ρητά, γράψε ακριβώς: «Δεν αναφέρεται καθαρά στο abstract.»
- Στο research_question διατύπωσε το ερώτημα μόνο όταν προκύπτει εύλογα από το abstract· διαφορετικά χρησιμοποίησε την παραπάνω φράση.
- Στο future_work ξεχώρισε όσα προτείνουν ρητά οι συγγραφείς από πιθανές επεκτάσεις. Μην παρουσιάζεις δική σου υπόθεση ως θέση των συγγραφέων.
- Στο datasets_vru_types_scenarios ανέφερε dataset names, τύπους VRU, περιβάλλον, sensors και σενάρια μόνο όταν αναφέρονται.
- relevance_score: ακέραιος 0–10 για VRU trajectory prediction, pedestrians, cyclists, micromobility, interactions, smart intersections, safety, intention και crossing behavior.
- relevance_label: 8–10 «Πολύ σχετικό», 5–7 «Μερικώς σχετικό», 0–4 «Χαμηλή συνάφεια».
"""


def call_llm(client: OpenAI, model: str, title: str, abstract: str, authors: List[str]) -> Dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Είσαι επιστημονικός βοηθός βιβλιογραφικής ανασκόπησης. Δεν επινοείς πληροφορίες που απουσιάζουν από την πηγή."},
            {"role": "user", "content": build_prompt(title, abstract, authors)},
        ],
    )
    return json.loads(response.choices[0].message.content)


def extract_candidate_papers(db: Dict[str, Any], summaries: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    papers = list((db.get("papers") or {}).values())
    papers.sort(key=lambda x: (x.get("published_utc", ""), x.get("title", "")), reverse=True)
    pending = [p for p in papers if p.get("arxiv_id") and p.get("arxiv_id") not in summaries]
    return pending[:limit]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/papers.json")
    ap.add_argument("--out", default="data/paper_summaries_el.json")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--limit", type=int, default=25, help="Αριθμός νέων, μη αναλυμένων papers ανά εκτέλεση")
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    db_path, out_path = Path(args.db), Path(args.out)
    db = read_json(db_path, {"papers": {}, "topics": {}})
    existing = read_json(out_path, {"summaries": {}})
    summaries = existing.get("summaries", {})
    papers = extract_candidate_papers(db, summaries, args.limit)

    print(f"Pending batch: {len(papers)} papers; already analyzed: {len(summaries)}")
    for paper in papers:
        arxiv_id = paper.get("arxiv_id")
        title = str(paper.get("title", "")).strip()
        abstract = str(paper.get("summary", "")).strip()
        if not arxiv_id or not title or not abstract:
            continue
        try:
            result = call_llm(client, args.model, title, abstract, paper.get("authors") or [])
            summaries[arxiv_id] = {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": paper.get("authors") or [],
                "published_utc": paper.get("published_utc", ""),
                "updated_utc": paper.get("updated_utc", ""),
                "primary_category": paper.get("primary_category", ""),
                "categories": paper.get("categories") or [],
                "abs_url": paper.get("abs_url", ""),
                "pdf_url": paper.get("pdf_url", ""),
                "analysis_source": "title_and_abstract",
                **result,
            }
            write_json(out_path, {"summaries": summaries})
            print(f"[OK] {arxiv_id} :: {title}")
            time.sleep(args.sleep)
        except Exception as exc:
            print(f"[ERROR] {arxiv_id} :: {exc}")

    write_json(out_path, {"summaries": summaries})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
