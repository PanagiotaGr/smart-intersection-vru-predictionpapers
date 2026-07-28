# Βάση γνώσης διπλωματικής — VRU trajectory prediction και IMPTC

Αυτός ο φάκελος δημιουργείται αυτόματα από το `scripts/build_thesis_knowledge_base.py` και οργανώνει τη βιβλιογραφία της διπλωματικής γύρω από:

- πρόβλεψη τροχιάς ευάλωτων χρηστών οδού,
- έξυπνες και σηματοδοτούμενες διασταυρώσεις,
- infrastructure-based sensing,
- multi-agent και interaction-aware prediction,
- deterministic, probabilistic και multimodal forecasting,
- δυνατότητα εφαρμογής κάθε paper στο IMPTC dataset.

## Παραγόμενη δομή

```text
thesis/
├── README.md
├── models/
│   ├── README.md
│   ├── gru.md
│   ├── lstm.md
│   ├── transformer.md
│   ├── gnn.md
│   ├── vae_cvae.md
│   ├── gan.md
│   ├── diffusion.md
│   └── ...
├── datasets/
│   ├── README.md
│   ├── imptc.md
│   ├── eth.md
│   ├── ucy.md
│   ├── stanford_drone_dataset.md
│   └── ...
├── prediction_types/
│   ├── deterministic.md
│   ├── probabilistic.md
│   ├── multimodal.md
│   ├── interaction_aware.md
│   ├── context_aware.md
│   └── intention_aware.md
├── comparisons/
│   ├── papers_matrix.md
│   └── datasets_matrix.md
└── json/
    ├── knowledge_base.json
    ├── model_index.json
    ├── dataset_index.json
    ├── prediction_type_index.json
    └── papers/<arxiv_id>.json
```

## Περιεχόμενο κάθε paper

Για κάθε paper διατηρούνται:

- τίτλος, συγγραφείς και αναγνωριστικά,
- ελληνική επιστημονική σύνοψη,
- ερευνητικό ερώτημα,
- στόχος και επιστημονική συνεισφορά,
- αναλυτική μεθοδολογία και αρχιτεκτονική,
- είσοδοι, έξοδοι και χαρακτηριστικά,
- deterministic/probabilistic/multimodal κατηγοριοποίηση,
- μοντέλα όπως GRU, LSTM, GNN, Transformer, CVAE, GAN και diffusion,
- datasets, τύποι VRU, sensors και context,
- evaluation protocol, baselines και metrics,
- αποτελέσματα και περιορισμοί,
- future work των συγγραφέων,
- δυνατότητα εφαρμογής στο IMPTC,
- απαιτούμενες προσαρμογές και πιθανή επέκταση για τη διπλωματική.

## Εκτέλεση

```bash
python scripts/build_thesis_knowledge_base.py
```

Η διαδικασία εκτελείται επίσης καθημερινά από το GitHub Action `Build Thesis Knowledge Base`.

## Επιστημονική ακεραιότητα

Η αυτόματη ανίχνευση όρων δείχνει ότι μια λέξη ή ονομασία εμφανίζεται στα διαθέσιμα metadata ή στην ελληνική ανάλυση. Δεν αποδεικνύει από μόνη της ότι η συγκεκριμένη τεχνική ή το dataset χρησιμοποιήθηκε πειραματικά.

Πριν από την τελική χρήση στη διπλωματική πρέπει να επιβεβαιώνονται από το πλήρες paper:

- η ακριβής αρχιτεκτονική,
- τα datasets και τα splits,
- οι observation/prediction horizons,
- οι baselines,
- οι loss functions,
- τα metrics και τα αριθμητικά αποτελέσματα,
- οι περιορισμοί και το future work των συγγραφέων.
