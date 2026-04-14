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


def build_prompt(title: str, abstract: str) -> str:
    return f"""
Διάβασε τα παρακάτω metadata από επιστημονικό paper και γράψε επιστημονική σύνοψη στα ελληνικά.

Τίτλος:
{title}

Abstract:
{abstract}

Επέστρεψε ΜΟΝΟ έγκυρο JSON με ακριβώς αυτά τα πεδία:
{{
  "short_summary_el": "...",
  "what_problem_does_it_solve": "...",
  "main_method": "...",
  "input_output": "...",
  "datasets_or_scenarios": "...",
  "key_results": "...",
  "limitations": "...",
  "why_it_matters_for_thesis": "...",
  "relevance_score": 0,
  "relevance_label": "...",
  "keywords_el": ["...", "...", "..."]
}}

Κανόνες:
- Γράψε στα ελληνικά.
- Να είναι σαφές τι κάνει το paper, όχι γενικόλογο.
- Αν κάτι δεν αναφέρεται καθαρά στο abstract, γράψε: "Δεν αναφέρεται καθαρά στο abstract."
- Το relevance_score να είναι από 0 έως 10.
- relevance_label:
  - 8 έως 10: "Πολύ σχετικό"
  - 5 έως 7: "Μερικώς σχετικό"
  - 0 έως 4: "Χαμηλή συνάφεια"
- Η συνάφεια να βασίζεται στο αν σχετίζεται με:
  VRU trajectory prediction, pedestrians, cyclists, micromobility,
  interaction-aware prediction, smart intersections, safety, intention, crossing behavior.
"""


def call_llm(client: OpenAI, model: str, title: str, abstract: str) -> Dict[str, Any]:
    prompt = build_prompt(title, abstract)

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    content = response.choices[0].message.content
    return json.loads(content)


def extract_candidate_papers(db: Dict[str, Any]) -> List[Dict[str, Any]]:
    papers = list((db.get("papers") or {}).values())
    papers.sort(key=lambda x: (x.get("published_utc", ""), x.get("title", "")), reverse=True)
    return papers


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/papers.json", help="Path to papers.json")
    ap.add_argument("--out", default="data/paper_summaries_el.json", help="Output summaries JSON")
    ap.add_argument("--model", default="gpt-4o-mini", help="OpenAI model")
    ap.add_argument("--limit", type=int, default=25, help="Max papers per run")
    ap.add_argument("--sleep", type=float, default=0.5, help="Sleep between API calls")
    args = ap.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    db_path = Path(args.db)
    out_path = Path(args.out)

    db = read_json(db_path, default={"papers": {}, "topics": {}})
    existing = read_json(out_path, default={"summaries": {}})

    summaries = existing.get("summaries", {})
    papers = extract_candidate_papers(db)[: args.limit]

    for paper in papers:
        arxiv_id = paper.get("arxiv_id")
        if not arxiv_id:
            continue
        if arxiv_id in summaries:
            continue

        title = paper.get("title", "").strip()
        abstract = paper.get("summary", "").strip()

        if not title or not abstract:
            continue

        try:
            result = call_llm(client, args.model, title, abstract)
            summaries[arxiv_id] = {
                "arxiv_id": arxiv_id,
                "title": title,
                "published_utc": paper.get("published_utc", ""),
                "primary_category": paper.get("primary_category", ""),
                "abs_url": paper.get("abs_url", ""),
                "pdf_url": paper.get("pdf_url", ""),
                **result,
            }
            print(f"[OK] {arxiv_id} :: {title}")
            write_json(out_path, {"summaries": summaries})
            time.sleep(args.sleep)
        except Exception as e:
            print(f"[ERROR] {arxiv_id} :: {e}")

    write_json(out_path, {"summaries": summaries})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
