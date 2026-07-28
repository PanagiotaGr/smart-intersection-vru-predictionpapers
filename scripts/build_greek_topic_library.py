#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def text(value: Any, default: str = "Δεν αναφέρεται καθαρά στο abstract.") -> str:
    value = str(value or "").strip()
    return value or default


def render_paper(item: dict[str, Any]) -> str:
    authors = ", ".join(item.get("authors") or []) or "Δεν υπάρχουν διαθέσιμα στοιχεία συγγραφέων."
    links = []
    if item.get("abs_url"):
        links.append(f"[Abstract]({item['abs_url']})")
    if item.get("pdf_url"):
        links.append(f"[PDF]({item['pdf_url']})")
    return "\n".join([
        f"## {text(item.get('title'), 'Χωρίς τίτλο')}",
        "",
        f"**Συγγραφείς:** {authors}",
        f"**arXiv ID:** `{text(item.get('arxiv_id'), '—')}`",
        f"**Ημερομηνία δημοσίευσης:** {text(item.get('published_utc'), '—')}",
        f"**Συνάφεια με τη διπλωματική:** {text(item.get('relevance_label'), '—')} ({item.get('relevance_score', 0)}/10)",
        f"**Σύνδεσμοι:** {' · '.join(links) if links else '—'}",
        "",
        "### Ελληνική σύνοψη",
        text(item.get("short_summary_el")),
        "",
        "### Ερευνητικό ερώτημα",
        text(item.get("research_question")),
        "",
        "### Στόχος και εργασία των συγγραφέων",
        text(item.get("authors_work_and_objective")),
        "",
        "### Πρόβλημα που αντιμετωπίζεται",
        text(item.get("what_problem_does_it_solve")),
        "",
        "### Μεθοδολογία",
        text(item.get("methodology_detailed") or item.get("main_method")),
        "",
        "### Είσοδοι και έξοδοι",
        text(item.get("input_output")),
        "",
        "### Datasets, VRU types και σενάρια",
        text(item.get("datasets_vru_types_scenarios") or item.get("datasets_or_scenarios")),
        "",
        "### Πειραματική αξιολόγηση και βασικά αποτελέσματα",
        text(item.get("evaluation_and_key_results") or item.get("key_results")),
        "",
        "### Επιστημονική συνεισφορά",
        text(item.get("scientific_contribution")),
        "",
        "### Περιορισμοί",
        text(item.get("limitations")),
        "",
        "### Μελλοντικές επεκτάσεις",
        text(item.get("future_work")),
        "",
        "### Χρησιμότητα για τη διπλωματική",
        text(item.get("why_it_matters_for_thesis")),
        "",
        "> **Σημείωση τεκμηρίωσης:** Η ανάλυση παράγεται από τίτλο και abstract. Πεδία που δεν δηλώνονται ρητά πρέπει να επιβεβαιώνονται από το πλήρες paper πριν χρησιμοποιηθούν ως ακαδημαϊκά τεκμήρια.",
        "",
        "---",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/papers.json")
    ap.add_argument("--summaries", default="data/paper_summaries_el.json")
    ap.add_argument("--outdir", default="topics/el")
    args = ap.parse_args()

    db = read_json(Path(args.db), {"papers": {}, "topics": {}})
    summary_data = read_json(Path(args.summaries), {"summaries": {}})
    papers = db.get("papers") or {}
    summaries = summary_data.get("summaries") or {}
    topics = db.get("topics") or {}
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().date().isoformat()

    index_lines = [
        "# Ελληνική Αναλυτική Βιβλιογραφική Βάση VRU",
        "",
        f"Τελευταία ενημέρωση: `{today}`",
        "",
        "Κάθε κατηγορία περιλαμβάνει όλα τα papers για τα οποία έχει παραχθεί ελληνική επιστημονική ανάλυση.",
        "",
        "| Κατηγορία | Αναλυμένα papers | Αρχείο |",
        "|---|---:|---|",
    ]

    for slug, topic in topics.items():
        ids = topic.get("paper_ids") or topic.get("papers") or []
        items = []
        for paper_id in ids:
            summary = summaries.get(paper_id)
            paper = papers.get(paper_id, {})
            if not summary:
                continue
            items.append({**paper, **summary})
        items.sort(key=lambda x: (x.get("published_utc", ""), x.get("title", "")), reverse=True)
        topic_name = topic.get("name") or slug.replace("_", " ").title()
        path = outdir / f"{slug}.md"
        lines = [
            f"# {topic_name} — Αναλυτική παρουσίαση στα ελληνικά",
            "",
            f"Τελευταία ενημέρωση: `{today}`",
            f"Αναλυμένα papers: **{len(items)}** από **{len(ids)}** καταχωρίσεις της κατηγορίας.",
            "",
            "---",
            "",
        ]
        for item in items:
            lines.append(render_paper(item))
        path.write_text("\n".join(lines), encoding="utf-8")
        index_lines.append(f"| {topic_name} | {len(items)} / {len(ids)} | [{slug}.md]({slug}.md) |")

    (outdir / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"[OK] Built Greek topic library in {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
