#!/usr/bin/env python3
"""Build a candidate VRU dataset catalogue from data/papers.json.

The script searches paper titles and abstracts for known dataset aliases. Its
output is a reproducible discovery layer, not a substitute for reading the
paper and the dataset documentation. Every generated row therefore contains a
verification_status field.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPERS_PATH = ROOT / "data" / "papers.json"
CSV_PATH = ROOT / "data" / "vru_datasets.csv"
MD_PATH = ROOT / "datasets" / "VRU_DATASET_CATALOG.md"

DATASETS: dict[str, dict[str, Any]] = {
    "ETH": {"aliases": [r"\bETH dataset\b", r"\bETH pedestrian\b"], "vru_types": "pedestrian", "task": "trajectory prediction"},
    "UCY": {"aliases": [r"\bUCY\b", r"\bZara0?1\b", r"\bZara0?2\b", r"\bUniversity Students\b"], "vru_types": "pedestrian", "task": "trajectory prediction"},
    "Stanford Drone Dataset": {"aliases": [r"\bStanford Drone Dataset\b", r"\bSDD\b"], "vru_types": "pedestrian; cyclist; skateboarder; cart; vehicle", "task": "trajectory prediction; interaction modelling"},
    "TrajNet++": {"aliases": [r"\bTrajNet\+\+\b", r"\bTrajNet\b"], "vru_types": "pedestrian", "task": "trajectory prediction benchmark"},
    "PIE": {"aliases": [r"\bPIE dataset\b", r"\bPedestrian Intention Estimation\b"], "vru_types": "pedestrian", "task": "crossing intention; trajectory prediction"},
    "JAAD": {"aliases": [r"\bJAAD\b", r"\bJoint Attention in Autonomous Driving\b"], "vru_types": "pedestrian", "task": "crossing intention; behaviour understanding"},
    "TITAN": {"aliases": [r"\bTITAN dataset\b"], "vru_types": "pedestrian; cyclist; motorcyclist; vehicle", "task": "action recognition; trajectory prediction"},
    "PedX": {"aliases": [r"\bPedX\b"], "vru_types": "pedestrian", "task": "3D pedestrian detection; tracking"},
    "JRDB": {"aliases": [r"\bJRDB\b"], "vru_types": "pedestrian", "task": "detection; tracking; social navigation"},
    "inD": {"aliases": [r"\binD dataset\b", r"\binD\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "intersection trajectories; interaction analysis"},
    "rounD": {"aliases": [r"\brounD\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "roundabout trajectories; interaction analysis"},
    "uniD": {"aliases": [r"\buniD\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "shared-space trajectories"},
    "INTERACTION": {"aliases": [r"\bINTERACTION dataset\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "motion forecasting; interaction modelling"},
    "nuScenes": {"aliases": [r"\bnuScenes\b"], "vru_types": "pedestrian; bicycle; motorcycle; vehicle", "task": "3D detection; tracking; prediction"},
    "Waymo Open Motion Dataset": {"aliases": [r"\bWaymo Open Motion Dataset\b", r"\bWOMD\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "motion forecasting"},
    "Waymo Open Dataset": {"aliases": [r"\bWaymo Open Dataset\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "3D perception; tracking"},
    "Argoverse 1": {"aliases": [r"\bArgoverse\b(?!\s*2)"], "vru_types": "pedestrian; cyclist; vehicle", "task": "motion forecasting; tracking"},
    "Argoverse 2": {"aliases": [r"\bArgoverse\s*2\b", r"\bAV2\b"], "vru_types": "pedestrian; cyclist; motorcyclist; vehicle", "task": "motion forecasting; 3D perception"},
    "Lyft Level 5": {"aliases": [r"\bLyft Level 5\b", r"\bLyft L5\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "motion forecasting"},
    "ApolloScape": {"aliases": [r"\bApolloScape\b"], "vru_types": "pedestrian; rider; vehicle", "task": "trajectory prediction; scene parsing"},
    "BDD100K": {"aliases": [r"\bBDD100K\b"], "vru_types": "pedestrian; rider; bicycle; motorcycle; vehicle", "task": "detection; tracking; segmentation"},
    "KITTI": {"aliases": [r"\bKITTI\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "detection; tracking; odometry"},
    "Cityscapes": {"aliases": [r"\bCityscapes\b"], "vru_types": "person; rider; bicycle; motorcycle", "task": "semantic and instance segmentation"},
    "EuroCity Persons": {"aliases": [r"\bEuroCity Persons\b", r"\bECP dataset\b"], "vru_types": "pedestrian; rider", "task": "pedestrian detection"},
    "Caltech Pedestrian": {"aliases": [r"\bCaltech Pedestrian\b"], "vru_types": "pedestrian", "task": "pedestrian detection"},
    "Daimler Pedestrian": {"aliases": [r"\bDaimler.*Pedestrian\b"], "vru_types": "pedestrian", "task": "pedestrian detection"},
    "Tsinghua-Daimler Cyclist": {"aliases": [r"\bTsinghua[- ]Daimler Cyclist\b"], "vru_types": "cyclist", "task": "cyclist detection"},
    "DADA-2000": {"aliases": [r"\bDADA[- ]2000\b"], "vru_types": "pedestrian; cyclist; motorcyclist; vehicle", "task": "traffic anomaly and accident analysis"},
    "DoTA": {"aliases": [r"\bDoTA dataset\b", r"\bDetection of Traffic Anomaly\b"], "vru_types": "pedestrian; cyclist; motorcyclist; vehicle", "task": "traffic anomaly detection"},
    "BLVD": {"aliases": [r"\bBLVD dataset\b"], "vru_types": "pedestrian; cyclist; vehicle", "task": "3D tracking; interaction and intention"},
}

CSV_FIELDS = [
    "dataset_name", "aliases", "vru_types", "primary_tasks",
    "paper_mentions", "paper_ids", "example_papers", "verification_status",
    "notes"
]


def load_papers() -> dict[str, dict[str, Any]]:
    payload = json.loads(PAPERS_PATH.read_text(encoding="utf-8"))
    return payload.get("papers", payload)


def find_mentions(papers: dict[str, dict[str, Any]]) -> dict[str, list[tuple[str, str]]]:
    mentions: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for paper_id, paper in papers.items():
        title = str(paper.get("title", ""))
        summary = str(paper.get("summary", ""))
        text = f"{title}\n{summary}"
        for dataset_name, metadata in DATASETS.items():
            if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in metadata["aliases"]):
                mentions[dataset_name].append((paper_id, title))
    return mentions


def build_rows(mentions: dict[str, list[tuple[str, str]]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, metadata in sorted(DATASETS.items()):
        found = mentions.get(name, [])
        rows.append({
            "dataset_name": name,
            "aliases": "; ".join(metadata["aliases"]),
            "vru_types": metadata["vru_types"],
            "primary_tasks": metadata["task"],
            "paper_mentions": str(len(found)),
            "paper_ids": "; ".join(paper_id for paper_id, _ in found),
            "example_papers": " | ".join(title for _, title in found[:5]),
            "verification_status": "candidate — verify against paper and official dataset documentation",
            "notes": "Automatically detected from title/abstract; absence of a mention does not prove non-use.",
        })
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# VRU Dataset Catalogue",
        "",
        "This catalogue is generated from dataset-name mentions in the tracked paper titles and abstracts.",
        "It is a discovery index: every entry must be verified from the full paper and the official dataset documentation.",
        "",
        "| Dataset | VRU types | Main tasks | Paper mentions | Status |",
        "|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['dataset_name']} | {row['vru_types']} | {row['primary_tasks']} | "
            f"{row['paper_mentions']} | candidate |"
        )
    lines.extend([
        "",
        "## Interpretation rules",
        "",
        "- `paper_mentions` counts explicit title/abstract mentions, not confirmed experimental use.",
        "- A paper may use a dataset only in its full text, so zero mentions is not proof of absence.",
        "- VRU labels follow the dataset's typical class taxonomy and should be checked against the exact release/version.",
        "- For thesis tables, confirm sensor setup, geography, scene type, annotations, sampling rate, splits, licence and evaluation protocol.",
        "",
        "The machine-readable version is available at `data/vru_datasets.csv`.",
    ])
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    papers = load_papers()
    mentions = find_mentions(papers)
    rows = build_rows(mentions)
    write_csv(rows)
    write_markdown(rows)
    print(f"Wrote {len(rows)} dataset records to {CSV_PATH} and {MD_PATH}")


if __name__ == "__main__":
    main()
