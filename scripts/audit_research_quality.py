#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_missing(value: Any) -> bool:
    if value is None or value == "" or value == [] or value == {}:
        return True
    if isinstance(value, str):
        text = value.strip().lower()
        return text in {
            "δεν αναφέρεται καθαρά στο abstract.",
            "δεν αναφέρεται.",
            "unknown",
            "not reported",
            "n/a",
        }
    return False


def evidence_level(record: dict[str, Any], levels: dict[str, int]) -> tuple[str, int]:
    raw = str(record.get("evidence_level") or record.get("analysis_source") or "metadata_only")
    normalized = raw.replace("title+abstract", "title_and_abstract")
    return normalized, levels.get(normalized, 0)


def score_record(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    required = schema["required_sections"]
    present = [field for field in required if not is_missing(record.get(field))]
    missing = [field for field in required if field not in present]
    evidence_name, evidence_rank = evidence_level(record, schema["evidence_levels"])

    dimensions = schema["quality_dimensions"]
    completeness = len(present) / max(1, len(required))
    score = completeness * dimensions["evidence_completeness"]

    groups = {
        "methodological_depth": ["methodology_detailed", "model_architecture_or_algorithm", "preprocessing", "loss_functions", "training_protocol"],
        "experimental_rigor": ["evaluation_protocol", "metrics", "baselines", "key_results", "statistical_significance", "ablation_studies", "robustness_analysis"],
        "reproducibility": ["training_protocol", "computational_complexity", "reproducibility_assets"],
        "dataset_transparency": ["datasets_vru_types_scenarios", "sensors_and_context", "input_output"],
        "metric_comparability": ["metrics", "evaluation_protocol", "key_results"],
        "limitations_and_validity": ["limitations", "threats_to_validity"],
        "imptc_transferability": ["imptc_applicability", "imptc_required_adaptations", "imptc_baseline_value", "thesis_research_opportunity"],
    }
    dimension_scores: dict[str, float] = {"evidence_completeness": round(completeness * dimensions["evidence_completeness"], 2)}
    for name, fields in groups.items():
        ratio = sum(not is_missing(record.get(field)) for field in fields) / len(fields)
        value = ratio * dimensions[name]
        dimension_scores[name] = round(value, 2)
        score += value

    evidence_cap = {0: 25, 1: 55, 2: 80, 3: 90, 4: 100}.get(evidence_rank, 25)
    score = min(round(score, 2), evidence_cap)
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "E"
    return {
        "paper_id": record.get("arxiv_id") or record.get("id") or "unknown",
        "title": record.get("title", ""),
        "quality_score": score,
        "quality_grade": grade,
        "evidence_level": evidence_name,
        "evidence_rank": evidence_rank,
        "dimension_scores": dimension_scores,
        "present_sections": len(present),
        "required_sections": len(required),
        "missing_sections": missing,
        "eligible_for_cross_paper_leaderboard": evidence_rank >= 2 and not any(is_missing(record.get(k)) for k in ["evaluation_protocol", "metrics", "key_results"]),
        "eligible_for_reproduction_claim": evidence_rank >= 4,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit scientific depth and evidence quality of every paper analysis.")
    parser.add_argument("--analyses", default="data/paper_analyses_el.json")
    parser.add_argument("--schema", default="config/research_quality_schema.json")
    parser.add_argument("--out", default="thesis/quality")
    args = parser.parse_args()

    schema = load_json(Path(args.schema), {})
    source = load_json(Path(args.analyses), {"analyses": {}})
    records = list((source.get("analyses") or {}).values())
    audits = [score_record(record, schema) for record in records]
    audits.sort(key=lambda item: (item["quality_score"], item["paper_id"]))

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    grades = Counter(item["quality_grade"] for item in audits)
    evidence = Counter(item["evidence_level"] for item in audits)
    report = {
        "schema_version": 1,
        "total_papers": len(audits),
        "average_quality_score": round(sum(item["quality_score"] for item in audits) / max(1, len(audits)), 2),
        "grade_distribution": dict(grades),
        "evidence_distribution": dict(evidence),
        "full_text_ready": sum(item["evidence_rank"] >= 2 for item in audits),
        "leaderboard_eligible": sum(item["eligible_for_cross_paper_leaderboard"] for item in audits),
        "audits": audits,
    }
    (output / "research_quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Έλεγχος επιστημονικής ποιότητας",
        "",
        f"- Papers: **{report['total_papers']}**",
        f"- Μέσο quality score: **{report['average_quality_score']}/100**",
        f"- Full-text evidence: **{report['full_text_ready']}**",
        f"- Επιλέξιμα για συγκρίσιμο leaderboard: **{report['leaderboard_eligible']}**",
        "",
        "## Κατανομή βαθμίδων",
        "",
        "| Βαθμίδα | Papers |",
        "|---|---:|",
    ]
    for grade in ["A", "B", "C", "D", "E"]:
        lines.append(f"| {grade} | {grades.get(grade, 0)} |")
    lines.extend(["", "## Papers που χρειάζονται προτεραιότητα", "", "| Paper | Score | Evidence | Κενά |", "|---|---:|---|---:|"])
    for item in audits[:100]:
        title = str(item["title"]).replace("|", "\\|")
        lines.append(f"| {title} | {item['quality_score']} | {item['evidence_level']} | {len(item['missing_sections'])} |")
    (output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
