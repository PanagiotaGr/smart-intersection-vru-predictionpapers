# Ελληνικό schema ανάλυσης papers με βάση το IMPTC

Η διπλωματική χρησιμοποιεί το **IMPTC — Infrastructural Multi-Person Trajectory and Context Dataset** ως βασικό dataset. Για τον λόγο αυτό, κάθε paper αναλύεται τόσο γενικά όσο και ως προς τη δυνατότητα εφαρμογής του στο IMPTC.

## Παραγόμενα JSON αρχεία

- `data/paper_analyses_el.json`: κεντρική βάση όλων των ελληνικών αναλύσεων.
- `data/papers_el/<arxiv_id>.json`: ανεξάρτητο JSON αρχείο για κάθε paper.

Τα αρχεία ενημερώνονται καθημερινά από το GitHub Actions workflow.

## Βασικά χαρακτηριστικά IMPTC που χρησιμοποιούνται στη σύγκριση

- roadside/infrastructure sensing σε δημόσια σηματοδοτούμενη αστική διασταύρωση,
- multi-view κάμερες και LiDAR,
- trajectories πεζών, ποδηλατών, μοτοσικλετιστών, χρηστών scooter και ατόμων με καρότσι,
- vehicle trajectories και multi-agent interactions,
- weather, traffic-light states, segmentation/ground map, OSM map και GPS timestamps,
- sequence-focused και trajectory-focused υποσύνολα,
- εφαρμογές single-VRU, multi-agent, interaction-aware και context-aware trajectory forecasting.

## Κύρια πεδία ανά paper

| Πεδίο | Περιεχόμενο |
|---|---|
| `short_summary_el` | Ελληνική επιστημονική σύνοψη |
| `research_question` | Ερευνητικό ερώτημα |
| `authors_work_and_objective` | Τι επιχειρούν οι συγγραφείς |
| `methodology_detailed` | Αναλυτική μεθοδολογία |
| `model_architecture_or_algorithm` | Μοντέλο ή αλγόριθμος |
| `datasets_vru_types_scenarios` | Datasets, VRU classes και σενάρια |
| `sensors_and_context` | Αισθητήρες και contextual δεδομένα |
| `evaluation_protocol` | Πειραματικό πρωτόκολλο |
| `metrics` | Μετρικές αξιολόγησης |
| `baselines` | Συγκρινόμενες μέθοδοι |
| `limitations` | Περιορισμοί |
| `future_work_authors` | Μελλοντική εργασία που δηλώνουν οι συγγραφείς |
| `future_extensions_for_imptc` | Προτεινόμενες επεκτάσεις για τη διπλωματική με IMPTC |
| `imptc_applicability` | Πώς μπορεί να εφαρμοστεί στο IMPTC |
| `imptc_required_adaptations` | Τι προσαρμογές χρειάζονται |
| `imptc_relevance_dimensions` | Επιμέρους βαθμολογίες συνάφειας |
| `imptc_relevance_score` | Συνολική βαθμολογία συνάφειας 0–10 |

## Επιστημονική ακεραιότητα

Η αυτοματοποιημένη ανάλυση βασίζεται αρχικά στον τίτλο και στο abstract. Όταν ένα στοιχείο δεν αναφέρεται ρητά, καταγράφεται ως μη διαθέσιμο. Metrics, datasets, baselines, αποτελέσματα και future work πρέπει να επιβεβαιώνονται από το πλήρες paper πριν χρησιμοποιηθούν ως τεκμήρια στη διπλωματική.
