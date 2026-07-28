#!/usr/bin/env python3
"""Build evidence-aware Greek systematic reviews for every Topic Navigator topic.

The generator is deliberately conservative: it organises existing structured
analyses and provenance records, but it never invents experimental findings.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def normalise_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("papers", "analyses", "records", "items"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
        return [v for v in payload.values() if isinstance(v, dict)]
    return []


def text_blob(record: dict[str, Any]) -> str:
    chunks: list[str] = []
    for value in record.values():
        if isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, list):
            chunks.extend(str(x) for x in value if isinstance(x, (str, int, float)))
    return " ".join(chunks).lower()


def topic_keywords(title: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]+", title.lower())
    stop = {"and", "for", "the", "aware", "models", "prediction", "forecasting", "general", "broad", "catch", "all"}
    return [w for w in words if len(w) > 3 and w not in stop]


def matches(record: dict[str, Any], title: str, slug: str) -> bool:
    blob = text_blob(record)
    explicit = record.get("topics") or record.get("topic") or record.get("categories")
    explicit_blob = json.dumps(explicit, ensure_ascii=False).lower() if explicit else ""
    keys = topic_keywords(title) + slug.split("-")
    hits = sum(1 for key in set(keys) if key in blob or key in explicit_blob)
    return hits >= 2


def get_list(record: dict[str, Any], *keys: str) -> list[str]:
    for key in keys:
        value = record.get(key)
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
    return []


def evidence_level(record: dict[str, Any]) -> str:
    return str(record.get("evidence_level") or record.get("source_level") or "metadata_or_abstract")


def safe_title(record: dict[str, Any]) -> str:
    return str(record.get("title") or record.get("paper_title") or record.get("id") or "Untitled paper")


def year_of(record: dict[str, Any]) -> str:
    value = record.get("year") or record.get("published") or record.get("date") or "Unknown"
    match = re.search(r"(19|20)\d{2}", str(value))
    return match.group(0) if match else "Unknown"


def render_review(topic: dict[str, Any], papers: list[dict[str, Any]], claims: list[dict[str, Any]]) -> str:
    title = topic["title"]
    slug = topic["slug"]
    selected = [p for p in papers if matches(p, title, slug)]
    selected.sort(key=lambda p: (year_of(p) == "Unknown", year_of(p), safe_title(p)), reverse=True)

    levels = Counter(evidence_level(p) for p in selected)
    years = Counter(year_of(p) for p in selected)
    models = Counter(x for p in selected for x in get_list(p, "model_families", "models", "architecture"))
    datasets = Counter(x for p in selected for x in get_list(p, "datasets", "dataset"))
    metrics = Counter(x for p in selected for x in get_list(p, "metrics", "evaluation_metrics"))
    limitations = [x for p in selected for x in get_list(p, "limitations", "limitation")]
    future = [x for p in selected for x in get_list(p, "future_work", "research_gaps")]
    imptc = [x for p in selected for x in get_list(p, "imptc_applicability", "imptc_adaptations")]

    topic_claims = [c for c in claims if isinstance(c, dict) and matches(c, title, slug)]
    supported_claims = [c for c in topic_claims if c.get("page") or c.get("table") or c.get("figure") or c.get("section")]

    def top(counter: Counter[str], n: int = 12) -> str:
        return ", ".join(f"{k} ({v})" for k, v in counter.most_common(n)) or "Δεν υπάρχουν ακόμη επαρκή δομημένα δεδομένα."

    lines = [
        f"# Systematic Review: {title}",
        "",
        f"**Τελευταία αναγέννηση:** {date.today().isoformat()}  ",
        f"**Papers που εντοπίστηκαν:** {len(selected)}  ",
        f"**Claims με page/section/table/figure provenance:** {len(supported_claims)}",
        "",
        "## 1. Scope and research questions",
        f"Η ανασκόπηση εξετάζει τη βιβλιογραφία της θεματικής **{title}** με έμφαση στη μοντελοποίηση, στα δεδομένα, στην πειραματική εγκυρότητα, στη συγκρισιμότητα και στη δυνατότητα μεταφοράς στο IMPTC.",
        "",
        "Κύρια ερωτήματα: ποια προβλήματα επιλύονται, ποιες οικογένειες μοντέλων κυριαρχούν, ποια contextual signals χρησιμοποιούνται, πόσο συγκρίσιμα είναι τα αποτελέσματα και ποια κενά μπορούν να αποτελέσουν ερευνητική συνεισφορά της διπλωματικής.",
        "",
        "## 2. Evidence coverage and review limitations",
        f"Επίπεδα τεκμηρίωσης: {top(levels, 8)}.",
        "",
        "Οι περιγραφές που βασίζονται μόνο σε metadata ή abstract δεν αντιμετωπίζονται ως πλήρης επαλήθευση μεθοδολογίας ή αποτελεσμάτων. Αριθμητικές συγκρίσεις επιτρέπονται μόνο όταν υπάρχει συμβατό protocol και provenance.",
        "",
        "## 3. Historical evolution",
        f"Κατανομή ανά έτος: {top(years, 20)}.",
        "",
        "## 4. Method taxonomy",
        f"Συχνότερες οικογένειες/αρχιτεκτονικές: {top(models)}.",
        "",
        "## 5. Inputs and contextual signals",
        "Η ενότητα ενημερώνεται από τα δομημένα πεδία inputs, sensors, context, intention, interaction, traffic lights, maps και weather των επιμέρους αναλύσεων. Όπου αυτά λείπουν, το κενό δηλώνεται αντί να συμπληρώνεται με υπόθεση.",
        "",
        "## 6. Datasets and experimental protocols",
        f"Συχνότερα datasets: {top(datasets)}.",
        "",
        "## 7. Metrics and comparability constraints",
        f"Συχνότερα metrics: {top(metrics)}.",
        "",
        "ADE/FDE και άλλα metrics δεν θεωρούνται άμεσα συγκρίσιμα όταν διαφέρουν prediction horizon, observation horizon, sampling rate, coordinate frame, split, agent filtering ή multimodal evaluation rule.",
        "",
        "## 8. Strongest supported findings",
    ]

    if supported_claims:
        for claim in supported_claims[:20]:
            locator = ", ".join(str(claim.get(k)) for k in ("page", "section", "table", "figure") if claim.get(k))
            lines.append(f"- {claim.get('claim') or claim.get('text') or 'Structured claim'} — **πηγή:** {locator}")
    else:
        lines.append("Δεν υπάρχουν ακόμη αρκετά full-text claims με ακριβές provenance για ασφαλή synthesis.")

    lines += [
        "",
        "## 9. Contradictory or inconclusive evidence",
        "Οι αντιφάσεις θα καταγράφονται μόνο όταν δύο ή περισσότερες πηγές χρησιμοποιούν επαρκώς παρόμοιο experimental protocol. Διαφορές σε dataset ή evaluation setup δεν χαρακτηρίζονται αυτόματα ως επιστημονική αντίφαση.",
        "",
        "## 10. Limitations and threats to validity",
    ]
    lines.extend(f"- {x}" for x in limitations[:25]) if limitations else lines.append("- Δεν έχουν εξαχθεί ακόμη επαρκείς limitations από full text.")
    lines += ["", "## 11. Open research gaps"]
    lines.extend(f"- {x}" for x in future[:25]) if future else lines.append("- Απαιτείται full-text review για αξιόπιστη εξαγωγή research gaps.")
    lines += ["", "## 12. IMPTC applicability"]
    lines.extend(f"- {x}" for x in imptc[:25]) if imptc else lines.append("- Να αξιολογηθούν camera/LiDAR fusion, traffic-light state, weather, multi-VRU interactions και infrastructure-view transfer.")
    lines += [
        "",
        "## 13. Thesis research opportunities",
        "- Δημιουργία protocol-compatible IMPTC baselines.",
        "- Ablation study για traffic lights, weather, maps και interaction context.",
        "- Αξιολόγηση deterministic, probabilistic και multimodal forecasting στο ίδιο split.",
        "- Calibration και uncertainty evaluation πέρα από ADE/FDE.",
        "- Cross-dataset generalisation και domain-shift analysis προς infrastructure sensing.",
        "",
        "## 14. Priority papers for full-text review",
        "",
        "| Year | Paper | Evidence | Priority reason |",
        "|---|---|---|---|",
    ]
    for paper in selected[:50]:
        level = evidence_level(paper)
        reason = "Full-text/provenance διαθέσιμο" if level in {"full_text", "full_text_plus_supplement", "reproduced"} else "Αναβάθμιση από abstract σε full text"
        lines.append(f"| {year_of(paper)} | {safe_title(paper).replace('|', '/')} | {level} | {reason} |")

    lines += [
        "",
        "## Review integrity statement",
        "Η σελίδα είναι evidence-aware systematic narrative review που παράγεται από τα διαθέσιμα structured records. Δεν αποτελεί PRISMA-complete systematic review έως ότου καταγραφούν search databases, exact queries, screening decisions, exclusion reasons και risk-of-bias assessment.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/systematic_topic_reviews.json")
    parser.add_argument("--analyses", default="data/paper_analyses_el.json")
    parser.add_argument("--claims", default="data/fulltext_research_records.json")
    parser.add_argument("--out", default="thesis/reviews")
    args = parser.parse_args()

    config = load_json(Path(args.config), {})
    papers = normalise_records(load_json(Path(args.analyses), []))
    claims = normalise_records(load_json(Path(args.claims), []))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    index = ["# Systematic Topic Reviews", "", "Evidence-aware reviews για τις θεματικές του Topic Navigator.", "", "| Topic | Review |", "|---|---|"]
    for topic in config.get("topics", []):
        if not isinstance(topic, dict) or not topic.get("slug") or not topic.get("title"):
            continue
        target = out / f"{topic['slug']}.md"
        target.write_text(render_review(topic, papers, claims), encoding="utf-8")
        index.append(f"| {topic['title']} | [{topic['slug']}.md]({topic['slug']}.md) |")

    (out / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"Generated {len(config.get('topics', []))} systematic topic reviews in {out}")


if __name__ == "__main__":
    main()
