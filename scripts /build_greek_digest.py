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


def render_entry(s: Dict[str, Any]) -> str:
    title = safe_str(s.get("title"), "Untitled")
    rel = safe_str(s.get("relevance_label"), "Άγνωστο")
    score = safe_int(s.get("relevance_score"), 0)

    abs_url = safe_str(s.get("abs_url"), "")
    pdf_url = safe_str(s.get("pdf_url"), "")

    short_summary = safe_str(s.get("short_summary_el"))
    problem = safe_str(s.get("what_problem_does_it_solve"))
    method = safe_str(s.get("main_method"))
    io_desc = safe_str(s.get("input_output"))
    datasets = safe_str(s.get("datasets_or_scenarios"))
    results = safe_str(s.get("key_results"))
    limitations = safe_str(s.get("limitations"))
    thesis_value = safe_str(s.get("why_it_matters_for_thesis"))
    published = safe_str(s.get("published_utc"), "Άγνωστη ημερομηνία")

    link_parts: List[str] = []
    if abs_url and abs_url != "—":
        link_parts.append(f"[Abstract]({abs_url})")
    if pdf_url and pdf_url != "—":
        link_parts.append(f"[PDF]({pdf_url})")
    links_line = " · ".join(link_parts) if link_parts else "—"

    return "\n".join(
        [
            f"## {title}",
            "",
            f"**Συνάφεια:** {rel} ({score}/10)",
            f"**Ημερομηνία:** {published}",
            "",
            "### Περίληψη στα ελληνικά",
            short_summary,
            "",
            "### Τι πρόβλημα λύνει",
            problem,
            "",
            "### Κύρια μέθοδος",
            method,
            "",
            "### Είσοδος / Έξοδος",
            io_desc,
            "",
            "### Δεδομένα / Σενάρια",
            datasets,
            "",
            "### Κύρια αποτελέσματα",
            results,
            "",
            "### Περιορισμοί",
            limitations,
            "",
            "### Γιατί είναι χρήσιμο για τη διπλωματική",
            thesis_value,
            "",
            f"**Links:** {links_line}",
            "",
            "---",
            "",
        ]
    )


def render_top_section(items: List[Dict[str, Any]], top_k: int = 3) -> List[str]:
    top_items = items[:top_k]
    if not top_items:
        return []

    lines = [
        "## Top papers της ημέρας",
        "",
    ]

    for idx, item in enumerate(top_items, start=1):
        title = safe_str(item.get("title"), "Untitled")
        score = safe_int(item.get("relevance_score"), 0)
        rel = safe_str(item.get("relevance_label"), "Άγνωστο")
        summary = safe_str(item.get("short_summary_el"))
        abs_url = safe_str(item.get("abs_url"), "")

        title_line = f"### {idx}. {title}"
        if abs_url and abs_url != "—":
            title_line = f"### {idx}. [{title}]({abs_url})"

        lines.extend(
            [
                title_line,
                f"**Συνάφεια:** {rel} ({score}/10)",
                "",
                summary,
                "",
            ]
        )

    lines.extend(["---", ""])
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Greek markdown digest from summarized papers.")
    ap.add_argument("--summaries", default="data/paper_summaries_el.json", help="Path to summaries JSON")
    ap.add_argument("--outdir", default="digests/el", help="Output directory")
    ap.add_argument("--min-score", type=int, default=6, help="Minimum relevance score to include")
    ap.add_argument("--limit", type=int, default=15, help="Maximum number of papers to include")
    ap.add_argument("--top-k", type=int, default=3, help="Number of top papers to highlight")
    args = ap.parse_args()

    summaries_path = Path(args.summaries)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    data = read_json(summaries_path, default={"summaries": {}})
    items: List[Dict[str, Any]] = list((data.get("summaries") or {}).values())

    items = [x for x in items if safe_int(x.get("relevance_score"), 0) >= args.min_score]
    items.sort(
        key=lambda x: (
            safe_int(x.get("relevance_score"), 0),
            safe_str(x.get("published_utc"), ""),
            safe_str(x.get("title"), "").lower(),
        ),
        reverse=True,
    )
    items = items[: args.limit]

    today = datetime.now().date().isoformat()
    out_file = outdir / f"{today}_el.md"

    lines = [
        f"# Ημερήσιο Ελληνικό Digest — {today}",
        "",
        "Αυτό το digest περιλαμβάνει papers από το arXiv σχετικά με πρόβλεψη τροχιάς VRUs,",
        "interaction-aware modeling, intention prediction, safety, και autonomous driving.",
        "",
        f"**Σύνολο papers:** {len(items)}",
        f"**Κατώφλι συνάφειας:** {args.min_score}/10",
        "",
        "---",
        "",
    ]

    lines.extend(render_top_section(items, top_k=args.top_k))

    for item in items:
        lines.append(render_entry(item))

    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
