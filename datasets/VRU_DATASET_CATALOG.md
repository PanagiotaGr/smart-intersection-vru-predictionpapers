# VRU Dataset Catalogue

This catalogue is generated from dataset-name mentions in the tracked paper titles and abstracts.
It is a discovery index: every entry must be verified from the full paper and the official dataset documentation.

| Dataset | VRU types | Main tasks | Paper mentions | Status |
|---|---|---|---:|---|
| ApolloScape | pedestrian; rider; vehicle | trajectory prediction; scene parsing | 3 | candidate |
| Argoverse 1 | pedestrian; cyclist; vehicle | motion forecasting; tracking | 28 | candidate |
| Argoverse 2 | pedestrian; cyclist; motorcyclist; vehicle | motion forecasting; 3D perception | 26 | candidate |
| BDD100K | pedestrian; rider; bicycle; motorcycle; vehicle | detection; tracking; segmentation | 0 | candidate |
| BLVD | pedestrian; cyclist; vehicle | 3D tracking; interaction and intention | 0 | candidate |
| Caltech Pedestrian | pedestrian | pedestrian detection | 0 | candidate |
| Cityscapes | person; rider; bicycle; motorcycle | semantic and instance segmentation | 0 | candidate |
| DADA-2000 | pedestrian; cyclist; motorcyclist; vehicle | traffic anomaly and accident analysis | 0 | candidate |
| Daimler Pedestrian | pedestrian | pedestrian detection | 0 | candidate |
| DoTA | pedestrian; cyclist; motorcyclist; vehicle | traffic anomaly detection | 0 | candidate |
| ETH | pedestrian | trajectory prediction | 0 | candidate |
| EuroCity Persons | pedestrian; rider | pedestrian detection | 0 | candidate |
| INTERACTION | pedestrian; cyclist; vehicle | motion forecasting; interaction modelling | 4 | candidate |
| JAAD | pedestrian | crossing intention; behaviour understanding | 30 | candidate |
| JRDB | pedestrian | detection; tracking; social navigation | 15 | candidate |
| KITTI | pedestrian; cyclist; vehicle | detection; tracking; odometry | 4 | candidate |
| Lyft Level 5 | pedestrian; cyclist; vehicle | motion forecasting | 0 | candidate |
| PIE | pedestrian | crossing intention; trajectory prediction | 5 | candidate |
| PedX | pedestrian | 3D pedestrian detection; tracking | 2 | candidate |
| Stanford Drone Dataset | pedestrian; cyclist; skateboarder; cart; vehicle | trajectory prediction; interaction modelling | 26 | candidate |
| TITAN | pedestrian; cyclist; motorcyclist; vehicle | action recognition; trajectory prediction | 0 | candidate |
| TrajNet++ | pedestrian | trajectory prediction benchmark | 2 | candidate |
| Tsinghua-Daimler Cyclist | cyclist | cyclist detection | 0 | candidate |
| UCY | pedestrian | trajectory prediction | 57 | candidate |
| Waymo Open Dataset | pedestrian; cyclist; vehicle | 3D perception; tracking | 5 | candidate |
| Waymo Open Motion Dataset | pedestrian; cyclist; vehicle | motion forecasting | 18 | candidate |
| inD | pedestrian; cyclist; vehicle | intersection trajectories; interaction analysis | 8 | candidate |
| nuScenes | pedestrian; bicycle; motorcycle; vehicle | 3D detection; tracking; prediction | 67 | candidate |
| rounD | pedestrian; cyclist; vehicle | roundabout trajectories; interaction analysis | 5 | candidate |
| uniD | pedestrian; cyclist; vehicle | shared-space trajectories | 0 | candidate |

## Interpretation rules

- `paper_mentions` counts explicit title/abstract mentions, not confirmed experimental use.
- A paper may use a dataset only in its full text, so zero mentions is not proof of absence.
- VRU labels follow the dataset's typical class taxonomy and should be checked against the exact release/version.
- For thesis tables, confirm sensor setup, geography, scene type, annotations, sampling rate, splits, licence and evaluation protocol.

The machine-readable version is available at `data/vru_datasets.csv`.
