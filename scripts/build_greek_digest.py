#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_str(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def relevance(item: Dict[str, Any]) -> tuple[str, int]:
    label = safe_str(item.get("imptc_relevance_label") or item.get("general_relevance_label") or item.get("relevance_label"), "Άγνωστο")
    score = safe_int(item.get("imptc_relevance_score", item.get("general_relevance_score", item.get("relevance_score", 0))))
    return label, score


def render_entry(s: Dict[str, Any]) -> str:
    title = safe_str(s.get("title"), "Untitled")
    rel, score = relevance(s)
    abs_url = safe_str(s.get("abs_url"), "")
    pdf_url = safe_str(s.get("pdf_url"), "")
    links: List[str] = []
    if abs_url and abs_url != "—":
        links.append(f"[Abstract]({abs_url})")
    if pdf_url and pdf_url != "—":
        links.append(f"[PDF]({pdf_url})")

    return "\n".join([
        f"## {title}",
        "",
        f"**Συνάφεια με IMPTC:** {rel} ({score}/10)",
        f"**Ημερομηνία:** {safe_str(s.get('published_utc'), 'Άγνωστη ημερομηνία')}",
        "",
        "### Περίληψη στα ελληνικά",
        safe_str(s.get("short_summary_el")),
        "",
        "### Ερευνητικό ερώτημα",
        safe_str(s.get("research_question")),
        "",
        "### Μεθοδολογία",
        safe_str(s.get("methodology_detailed") or s.get("main_method")),
        "",
        "### Εφαρμοσιμότητα στο IMPTC",
        safe_str(s.get("imptc_applicability") or s.get("why_it_matters_for_thesis")),
        "",
        "### Προτεινόμενες επεκτάσεις για IMPTC",
        safe_str(s.get("future_extensions_for_imptc")),
        "",
        f"**Links:** {' · '.join(links) if links else '—'}",
        "",
        "---",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Greek IMPTC-aware markdown digest.")
    ap.add_argument("--summaries", default="data/paper_analyses_el.json")
    ap.add_argument("--outdir", default="digests/el")
    ap.add_argument("--min-score", type=int, default=0)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    data = read_json(Path(args.summaries), default={"analyses": {}})
    records = data.get("analyses") or data.get("summaries") or {}
    items: List[Dict[str, Any]] = list(records.values())
    items = [item for item in items if relevance(item)[1] >= args.min_score]
    items.sort(key=lambda item: (relevance(item)[1], safe_str(item.get("published_utc"), "")), reverse=True)
    items = items[: args.limit]

    today = datetime.now().date().isoformat()
    lines = [
        f"# Ημερήσιο Ελληνικό IMPTC-aware Digest — {today}",
        "",
        "Το digest ταξινομεί τις διαθέσιμες ελληνικές αναλύσεις με βάση τη συνάφεια προς το IMPTC dataset.",
        "",
        f"**Σύνολο papers:** {len(items)}",
        f"**Κατώφλι συνάφειας IMPTC:** {args.min_score}/10",
        "",
        "---",
        "",
    ]
    for item in items:
        lines.append(render_entry(item))

    out_file = outdir / f"{today}_el.md"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
