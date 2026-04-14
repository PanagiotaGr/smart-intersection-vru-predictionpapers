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


def render_entry(s: Dict[str, Any]) -> str:
    title = s.get("title", "Untitled")
    rel = s.get("relevance_label", "Άγνωστο")
    score = s.get("relevance_score", "n/a")
    abs_url = s.get("abs_url", "")
    pdf_url = s.get("pdf_url", "")

    lines = [
        f"## {title}",
        "",
        f"**Συνάφεια:** {rel} ({score}/10)",
        "",
        f"**Τι μελετά:** {s.get('short_summary_el', '—')}",
        "",
        f"**Ποιο πρόβλημα λύνει:** {s.get('what_problem_does_it_solve', '—')}",
        "",
        f"**Κύρια μέθοδος:** {s.get('main_method', '—')}",
        "",
        f"**Είσοδος / Έξοδος:** {s.get('input_output', '—')}",
        "",
        f"**Δεδομένα / Σενάρια:** {s.get('datasets_or_scenarios', '—')}",
        "",
        f"**Κύρια αποτελέσματα:** {s.get('key_results', '—')}",
        "",
        f"**Περιορισμοί:** {s.get('limitations', '—')}",
        "",
        f"**Γιατί είναι χρήσιμο για τη διπλωματική:** {s.get('why_it_matters_for_thesis', '—')}",
        "",
        f"**Links:** [abs]({abs_url}) · [pdf]({pdf_url})" if abs_url or pdf_url else "",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summaries", default="data/paper_summaries_el.json")
    ap.add_argument("--outdir", default="digests/el")
    ap.add_argument("--min-score", type=int, default=6)
    ap.add_argument("--limit", type=int, default=15)
    args = ap.parse_args()

    summaries_path = Path(args.summaries)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    data = read_json(summaries_path, default={"summaries": {}})
    items: List[Dict[str, Any]] = list((data.get("summaries") or {}).values())

    items = [x for x in items if int(x.get("relevance_score", 0)) >= args.min_score]
    items.sort(key=lambda x: (int(x.get("relevance_score", 0)), x.get("published_utc", "")), reverse=True)
    items = items[: args.limit]

    today = datetime.now().date().isoformat()
    out_file = outdir / f"{today}_el.md"

    lines = [
        f"# Ημερήσιο Ελληνικό Digest — {today}",
        "",
        f"Σύνολο papers: **{len(items)}**",
        "",
        "---",
        "",
    ]

    for item in items:
        lines.append(render_entry(item))

    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
