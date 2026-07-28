#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(x) for x in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {norm(v)}" for k, v in value.items())
    return str(value or "")


def slugify(value: str) -> str:
    value = value.lower().strip().replace("++", "_plusplus")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "unknown"


def matches(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    return sorted({term for term in terms if term.lower() in lower})


def classify_paper(paper: dict[str, Any], taxonomy: dict[str, Any]) -> dict[str, Any]:
    searchable = norm(paper)
    model_hits = {
        family: matches(searchable, terms)
        for family, terms in taxonomy.get("model_families", {}).items()
    }
    model_hits = {k: v for k, v in model_hits.items() if v}

    prediction_hits = {
        kind: matches(searchable, terms)
        for kind, terms in taxonomy.get("prediction_types", {}).items()
    }
    prediction_hits = {k: v for k, v in prediction_hits.items() if v}

    datasets = []
    for dataset in taxonomy.get("dataset_registry", []):
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(dataset)}(?![A-Za-z0-9])", searchable, re.IGNORECASE):
            datasets.append(dataset)

    metrics = matches(searchable, taxonomy.get("metrics", []))

    return {
        "model_families": sorted(model_hits),
        "model_evidence": model_hits,
        "prediction_types": sorted(prediction_hits),
        "prediction_evidence": prediction_hits,
        "datasets": sorted(set(datasets)),
        "metrics": metrics,
    }


def render_paper(paper: dict[str, Any], cls: dict[str, Any]) -> str:
    def field(name: str, fallback: str = "Δεν αναφέρεται καθαρά στο abstract.") -> str:
        return str(paper.get(name) or fallback).strip()

    authors = ", ".join(paper.get("authors") or []) or "Δεν υπάρχουν διαθέσιμα στοιχεία."
    return "\n".join([
        f"## {paper.get('title', 'Χωρίς τίτλο')}",
        "",
        f"**Συγγραφείς:** {authors}",
        f"**arXiv ID:** `{paper.get('arxiv_id', '—')}`",
        f"**Οικογένειες μοντέλων:** {', '.join(cls['model_families']) or 'Δεν ανιχνεύθηκαν αυτόματα'}",
        f"**Τύπος πρόβλεψης:** {', '.join(cls['prediction_types']) or 'Δεν ανιχνεύθηκε αυτόματα'}",
        f"**Datasets:** {', '.join(cls['datasets']) or 'Δεν ανιχνεύθηκαν αυτόματα'}",
        f"**Metrics:** {', '.join(cls['metrics']) or 'Δεν ανιχνεύθηκαν αυτόματα'}",
        f"**Συνάφεια IMPTC:** {paper.get('imptc_relevance_label', paper.get('relevance_label', '—'))} ({paper.get('imptc_relevance_score', paper.get('relevance_score', 0))}/10)",
        "",
        "### Ελληνική σύνοψη",
        field("short_summary_el"),
        "",
        "### Ερευνητικό ερώτημα",
        field("research_question"),
        "",
        "### Μεθοδολογία και αρχιτεκτονική",
        field("methodology_detailed", field("main_method")),
        "",
        "### Πειραματικά δεδομένα, VRUs και αισθητήρες",
        field("datasets_vru_types_scenarios", field("datasets_or_scenarios")),
        "",
        "### Αξιολόγηση και αποτελέσματα",
        field("evaluation_and_key_results", field("key_results")),
        "",
        "### Περιορισμοί",
        field("limitations"),
        "",
        "### Μελλοντική εργασία συγγραφέων",
        field("future_work_authors", field("future_work")),
        "",
        "### Εφαρμογή στο IMPTC",
        field("imptc_applicability", field("why_it_matters_for_thesis")),
        "",
        "### Απαραίτητες προσαρμογές για IMPTC",
        field("imptc_required_adaptations"),
        "",
        "### Προτεινόμενη επέκταση για τη διπλωματική",
        field("future_extensions_for_imptc"),
        "",
        "> Η αυτόματη ταξινόμηση και η ελληνική ανάλυση πρέπει να επιβεβαιώνονται από το πλήρες paper πριν χρησιμοποιηθούν ως τελικό ακαδημαϊκό τεκμήριο.",
        "",
        "---",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an IMPTC-centred Greek thesis knowledge base.")
    parser.add_argument("--papers", default="data/papers.json")
    parser.add_argument("--analyses", default="data/paper_analyses_el.json")
    parser.add_argument("--fallback-analyses", default="data/paper_summaries_el.json")
    parser.add_argument("--taxonomy", default="config/thesis_taxonomy.json")
    parser.add_argument("--out", default="thesis")
    args = parser.parse_args()

    papers_db = read_json(Path(args.papers), {"papers": {}}).get("papers", {})
    analyses_payload = read_json(Path(args.analyses), {})
    analyses = analyses_payload.get("analyses") or analyses_payload.get("summaries") or {}
    if not analyses:
        fallback = read_json(Path(args.fallback_analyses), {"summaries": {}})
        analyses = fallback.get("summaries", {})
    taxonomy = read_json(Path(args.taxonomy), {})
    out = Path(args.out)

    records: dict[str, Any] = {}
    by_model: dict[str, list[str]] = defaultdict(list)
    by_dataset: dict[str, list[str]] = defaultdict(list)
    by_prediction: dict[str, list[str]] = defaultdict(list)

    for paper_id, analysis in analyses.items():
        source = papers_db.get(paper_id, {})
        paper = {**source, **analysis}
        paper.setdefault("arxiv_id", paper_id)
        cls = classify_paper(paper, taxonomy)
        records[paper_id] = {"paper": paper, "classification": cls}
        for name in cls["model_families"]:
            by_model[name].append(paper_id)
        for name in cls["datasets"]:
            by_dataset[name].append(paper_id)
        for name in cls["prediction_types"]:
            by_prediction[name].append(paper_id)

    generated_at = datetime.now(timezone.utc).isoformat()
    write_json(out / "json" / "knowledge_base.json", {
        "schema_version": "1.0",
        "generated_at_utc": generated_at,
        "thesis_focus": taxonomy.get("thesis_focus"),
        "paper_count": len(records),
        "papers": records,
        "indexes": {
            "by_model": dict(sorted(by_model.items())),
            "by_dataset": dict(sorted(by_dataset.items())),
            "by_prediction_type": dict(sorted(by_prediction.items())),
        },
    })
    write_json(out / "json" / "model_index.json", dict(sorted(by_model.items())))
    write_json(out / "json" / "dataset_index.json", dict(sorted(by_dataset.items())))
    write_json(out / "json" / "prediction_type_index.json", dict(sorted(by_prediction.items())))

    for paper_id, record in records.items():
        safe_id = slugify(paper_id.replace(".", "_"))
        write_json(out / "json" / "papers" / f"{safe_id}.json", record)

    index_lines = [
        "# Βάση γνώσης διπλωματικής — VRU trajectory prediction και IMPTC",
        "",
        f"Τελευταία δημιουργία: `{generated_at}`",
        f"Αναλυμένα papers: **{len(records)}**",
        "",
        "## Ευρετήρια",
        "",
        "- [Μοντέλα και αρχιτεκτονικές](models/README.md)",
        "- [Datasets](datasets/README.md)",
        "- [Τύποι πρόβλεψης](prediction_types/README.md)",
        "- [Συγκριτικός πίνακας papers](comparisons/papers_matrix.md)",
        "- [Συγκριτικός πίνακας datasets](comparisons/datasets_matrix.md)",
        "- [JSON knowledge base](json/knowledge_base.json)",
        "",
    ]
    (out / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text("\n".join(index_lines), encoding="utf-8")

    for folder, mapping, title in [
        ("models", by_model, "Μοντέλα και αρχιτεκτονικές"),
        ("datasets", by_dataset, "Datasets"),
        ("prediction_types", by_prediction, "Τύποι πρόβλεψης"),
    ]:
        base = out / folder
        base.mkdir(parents=True, exist_ok=True)
        listing = [f"# {title}", "", "| Κατηγορία | Papers | Αρχείο |", "|---|---:|---|"]
        for key, ids in sorted(mapping.items()):
            filename = f"{slugify(key)}.md"
            lines = [f"# {key}", "", f"Σύνολο papers: **{len(ids)}**", "", "---", ""]
            for paper_id in sorted(ids, key=lambda x: records[x]["paper"].get("published_utc", ""), reverse=True):
                lines.append(render_paper(records[paper_id]["paper"], records[paper_id]["classification"]))
            (base / filename).write_text("\n".join(lines), encoding="utf-8")
            listing.append(f"| {key} | {len(ids)} | [{filename}]({filename}) |")
        (base / "README.md").write_text("\n".join(listing) + "\n", encoding="utf-8")

    comparison_dir = out / "comparisons"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    paper_rows = [
        "# Συγκριτικός πίνακας papers",
        "",
        "| Paper | Μοντέλα | Τύπος πρόβλεψης | Datasets | Metrics | IMPTC score |",
        "|---|---|---|---|---|---:|",
    ]
    for paper_id, record in sorted(records.items(), key=lambda kv: kv[1]["paper"].get("published_utc", ""), reverse=True):
        paper, cls = record["paper"], record["classification"]
        title = str(paper.get("title", paper_id)).replace("|", "\\|")
        paper_rows.append(
            f"| {title} | {', '.join(cls['model_families']) or '—'} | {', '.join(cls['prediction_types']) or '—'} | "
            f"{', '.join(cls['datasets']) or '—'} | {', '.join(cls['metrics']) or '—'} | "
            f"{paper.get('imptc_relevance_score', paper.get('relevance_score', 0))} |"
        )
    (comparison_dir / "papers_matrix.md").write_text("\n".join(paper_rows) + "\n", encoding="utf-8")

    dataset_rows = [
        "# Συγκριτικός πίνακας datasets",
        "",
        "Ο πίνακας καταγράφει datasets που ανιχνεύθηκαν στις υπάρχουσες αναλύσεις. Τα τεχνικά χαρακτηριστικά τους πρέπει να επαληθεύονται από την επίσημη δημοσίευση και τεκμηρίωση.",
        "",
        "| Dataset | Πλήθος papers | Papers |",
        "|---|---:|---|",
    ]
    for dataset, ids in sorted(by_dataset.items()):
        titles = [records[x]["paper"].get("title", x) for x in ids[:8]]
        dataset_rows.append(f"| {dataset} | {len(ids)} | {'; '.join(titles)} |")
    (comparison_dir / "datasets_matrix.md").write_text("\n".join(dataset_rows) + "\n", encoding="utf-8")

    print(f"[OK] Built thesis knowledge base with {len(records)} papers in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
