#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


IMPTC_PROFILE = {
    "name": "IMPTC — Infrastructural Multi-Person Trajectory and Context Dataset",
    "scene": "δημόσια, σηματοδοτούμενη αστική διασταύρωση στη Γερμανία",
    "viewpoint": "υποδομή / roadside sensing",
    "sensors": ["πολλαπλές κάμερες", "LiDAR", "αισθητήρες καιρού", "καταστάσεις φωτεινών σηματοδοτών"],
    "frequency": "25 Hz για τα βασικά συγχρονισμένα δεδομένα",
    "vru_types": ["πεζοί", "ποδηλάτες", "μοτοσικλετιστές", "χρήστες scooter", "άτομα με καρότσι", "χρήστες αναπηρικού αμαξιδίου"],
    "context": ["καιρός", "φωτισμός", "σήματα κυκλοφορίας", "segmentation/ground map", "OSM map", "GPS timestamps"],
    "research_targets": ["πρόβλεψη τροχιάς ενός VRU", "multi-agent trajectory forecasting", "interaction-aware forecasting", "scene understanding", "context-aware prediction"],
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._") or "paper"


def build_prompt(title: str, abstract: str, authors: List[str]) -> str:
    profile = json.dumps(IMPTC_PROFILE, ensure_ascii=False, indent=2)
    return f"""
Ανάλυσε επιστημονικά το παρακάτω paper στα ελληνικά, χρησιμοποιώντας αποκλειστικά όσα τεκμηριώνονται από τον τίτλο και το abstract.
Η διπλωματική εργασία χρησιμοποιεί το IMPTC dataset. Χρησιμοποίησε το ακόλουθο επιβεβαιωμένο προφίλ μόνο για συγκριτική αξιολόγηση συνάφειας και εφαρμοσιμότητας, όχι για να αποδώσεις στο paper στοιχεία που δεν αναφέρει:
{profile}

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
  "model_architecture_or_algorithm": "...",
  "input_output": "...",
  "datasets_or_scenarios": "...",
  "datasets_vru_types_scenarios": "...",
  "sensors_and_context": "...",
  "evaluation_protocol": "...",
  "metrics": "...",
  "baselines": "...",
  "key_results": "...",
  "evaluation_and_key_results": "...",
  "scientific_contribution": "...",
  "limitations": "...",
  "future_work_authors": "...",
  "future_extensions_for_imptc": "...",
  "why_it_matters_for_thesis": "...",
  "imptc_applicability": "...",
  "imptc_required_adaptations": "...",
  "imptc_relevance_dimensions": {{
    "infrastructure_sensing": 0,
    "multi_agent_interactions": 0,
    "trajectory_forecasting": 0,
    "scene_context": 0,
    "traffic_signal_context": 0,
    "weather_context": 0,
    "vru_class_coverage": 0,
    "smart_intersection_setting": 0
  }},
  "imptc_relevance_score": 0,
  "imptc_relevance_label": "...",
  "general_relevance_score": 0,
  "general_relevance_label": "...",
  "evidence_level": "title_and_abstract",
  "keywords_el": ["...", "...", "..."]
}}

Κανόνες:
- Όλο το κείμενο να είναι στα ελληνικά, με ακαδημαϊκό και σαφή λόγο.
- Μην επινοείς datasets, metrics, αποτελέσματα, αρχιτεκτονικές, baselines, περιορισμούς ή future work.
- Όταν κάτι δεν δηλώνεται ρητά, γράψε ακριβώς: «Δεν αναφέρεται καθαρά στο abstract.»
- Το future_work_authors περιλαμβάνει μόνο όσα προτείνουν ρητά οι συγγραφείς.
- Το future_extensions_for_imptc μπορεί να περιλαμβάνει τεκμηριωμένες προτεινόμενες εφαρμογές ή προσαρμογές για IMPTC, αλλά να δηλώνεται καθαρά ότι είναι πρόταση για τη διπλωματική και όχι θέση των συγγραφέων.
- Κάθε διάσταση IMPTC βαθμολογείται με ακέραιο 0–10 βάσει των στοιχείων του paper.
- imptc_relevance_score: ακέραιος 0–10. 8–10 «Πολύ υψηλή συνάφεια με IMPTC», 5–7 «Μέτρια συνάφεια με IMPTC», 0–4 «Χαμηλή συνάφεια με IMPTC».
- general_relevance_score: ακέραιος 0–10 για VRU trajectory prediction, pedestrians, cyclists, micromobility, interactions, smart intersections, safety, intention και crossing behavior.
- general_relevance_label: 8–10 «Πολύ σχετικό», 5–7 «Μερικώς σχετικό», 0–4 «Χαμηλή συνάφεια».
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


def extract_candidate_papers(db: Dict[str, Any], analyses: Dict[str, Any], limit: int, refresh_existing: bool) -> List[Dict[str, Any]]:
    papers = list((db.get("papers") or {}).values())
    papers.sort(key=lambda x: (x.get("published_utc", ""), x.get("title", "")), reverse=True)
    if refresh_existing:
        return [p for p in papers if p.get("arxiv_id")][:limit]
    pending = [p for p in papers if p.get("arxiv_id") and p.get("arxiv_id") not in analyses]
    return pending[:limit]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/papers.json")
    ap.add_argument("--out", default="data/paper_analyses_el.json")
    ap.add_argument("--legacy-out", default="data/paper_summaries_el.json")
    ap.add_argument("--paper-dir", default="data/papers_el")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--limit", type=int, default=25, help="Αριθμός νέων, μη αναλυμένων papers ανά εκτέλεση")
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--refresh-existing", action="store_true", help="Επαναδημιουργία υπαρχουσών αναλύσεων με το νέο schema")
    args = ap.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    db_path = Path(args.db)
    out_path = Path(args.out)
    legacy_path = Path(args.legacy_out)
    paper_dir = Path(args.paper_dir)

    db = read_json(db_path, {"papers": {}, "topics": {}})
    existing = read_json(out_path, {"schema_version": 2, "imptc_profile": IMPTC_PROFILE, "analyses": {}})
    analyses = existing.get("analyses", {})

    legacy = read_json(legacy_path, {"summaries": {}})
    legacy_summaries = legacy.get("summaries", {})
    for paper_id, summary in legacy_summaries.items():
        analyses.setdefault(paper_id, summary)

    papers = extract_candidate_papers(db, analyses, args.limit, args.refresh_existing)
    print(f"Pending batch: {len(papers)} papers; already analyzed: {len(analyses)}")

    for paper in papers:
        arxiv_id = paper.get("arxiv_id")
        title = str(paper.get("title", "")).strip()
        abstract = str(paper.get("summary", "")).strip()
        if not arxiv_id or not title or not abstract:
            continue
        try:
            result = call_llm(client, args.model, title, abstract, paper.get("authors") or [])
            record = {
                "schema_version": 2,
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": paper.get("authors") or [],
                "published_utc": paper.get("published_utc", ""),
                "updated_utc": paper.get("updated_utc", ""),
                "primary_category": paper.get("primary_category", ""),
                "categories": paper.get("categories") or [],
                "abs_url": paper.get("abs_url", ""),
                "pdf_url": paper.get("pdf_url", ""),
                "source_abstract": abstract,
                "analysis_source": "title_and_abstract",
                "thesis_dataset": "IMPTC",
                **result,
            }
            analyses[arxiv_id] = record
            payload = {
                "schema_version": 2,
                "imptc_profile": IMPTC_PROFILE,
                "analyses": analyses,
            }
            write_json(out_path, payload)
            write_json(paper_dir / f"{safe_filename(arxiv_id)}.json", record)
            print(f"[OK] {arxiv_id} :: {title}")
            time.sleep(args.sleep)
        except Exception as exc:
            print(f"[ERROR] {arxiv_id} :: {exc}")

    write_json(out_path, {"schema_version": 2, "imptc_profile": IMPTC_PROFILE, "analyses": analyses})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
