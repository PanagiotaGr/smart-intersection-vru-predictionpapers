# VRU Datasets — Thesis Extraction Guide

This directory separates **dataset evidence** from the daily paper digest. The goal is to build a thesis-ready table describing every dataset found in the tracked literature, what it was created for, and which vulnerable road-user classes it contains.

## Generated outputs

Run:

```bash
python scripts/build_dataset_catalog.py
```

The command reads `data/papers.json` and creates:

- `data/vru_datasets.csv`: machine-readable dataset matrix.
- `datasets/VRU_DATASET_CATALOG.md`: readable catalogue with mention counts.

## Required thesis fields

The automatic extractor supplies candidate dataset names, common VRU types, task categories and paper mentions. During full-paper review, extend each dataset entry with:

| Field | What to record |
|---|---|
| Dataset / version | Exact official name and release/version |
| Original publication | Dataset paper, DOI/arXiv and year |
| Purpose | Why the dataset was collected and its intended tasks |
| Environment | Intersection, road, shared space, campus, roundabout or general urban scene |
| Geography | Country/city and number of recording locations |
| VRU types | Pedestrian, cyclist, motorcyclist, scooter/micromobility, wheelchair user, skateboarder, etc. |
| Other agents | Cars, buses, trucks, carts and other interacting agents |
| Sensors | RGB, stereo, thermal, LiDAR, radar, drone, infrastructure camera, ego vehicle |
| Viewpoint | Ego-centric, roadside/infrastructure, aerial or static surveillance |
| Scale | Number of scenes, sequences, agents, tracks, frames and duration |
| Sampling | Frame rate and trajectory sampling frequency |
| Annotations | 2D/3D boxes, tracks, poses, actions, crossing state, intention, gaze, traffic lights, maps |
| Prediction task | Trajectory, destination, intention, action, risk, collision or gap acceptance |
| Forecast protocol | Observation/prediction horizon and coordinate system |
| Splits | Official train/validation/test split and cross-scene protocol |
| Metrics | ADE, FDE, minADE, minFDE, miss rate, accuracy, F1, TTC or other metrics |
| Access | Public/restricted, licence and download location |
| Limitations | Bias, class imbalance, weather/time coverage, privacy, annotation uncertainty |
| Thesis relevance | Direct/core, supporting, benchmark-only or out of scope |

## VRU taxonomy

Use normalized labels so datasets remain comparable:

- `pedestrian`
- `cyclist`
- `motorcyclist`
- `micromobility` (e-scooter and similar devices)
- `wheelchair_user`
- `skateboarder`
- `other_vru`

Keep the dataset's original label in a separate field when it uses broader labels such as `person`, `rider` or `two-wheeler`.

## Evidence levels

1. **Candidate** — dataset name appears in a title or abstract.
2. **Confirmed use** — the experimental section confirms that the paper uses the dataset.
3. **Officially verified** — dataset properties were checked against its official paper or documentation.

Do not report automatically inferred fields as confirmed facts until evidence level 2 or 3 is reached.
