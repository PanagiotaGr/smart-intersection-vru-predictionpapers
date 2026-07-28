# PhD-grade πλατφόρμα βιβλιογραφικής έρευνας

Ο στόχος του repository δεν είναι να λειτουργεί ως απλό αρχείο papers. Πρέπει να αποτελεί ελεγχόμενη, επαναλήψιμη και επιστημονικά τεκμηριωμένη βάση γνώσης για trajectory prediction ευάλωτων χρηστών οδικού δικτύου και για πειράματα στο IMPTC.

## Πέντε επίπεδα τεκμηρίωσης

1. `metadata_only`: τίτλος, συγγραφείς και βιβλιογραφικά μεταδεδομένα.
2. `title_and_abstract`: ανάλυση βασισμένη αποκλειστικά σε τίτλο και abstract.
3. `full_text`: επιβεβαίωση από το πλήρες paper με σελίδες, ενότητες, πίνακες και σχήματα.
4. `full_text_plus_supplement`: paper, appendix, supplementary material και επίσημος κώδικας.
5. `reproduced`: το πείραμα εκτελέστηκε και τα αποτελέσματα ελέγχθηκαν.

Κάθε ισχυρισμός πρέπει να δηλώνει το επίπεδο τεκμηρίωσής του. Μια abstract-based ανάλυση δεν επιτρέπεται να εμφανίζεται ως ισοδύναμη με full-text extraction ή reproduction.

## Ερευνητικός φάκελος ανά paper

Ο πλήρης φάκελος πρέπει να περιλαμβάνει:

- ερευνητικό ερώτημα, motivation, literature gap και hypotheses,
- αρχιτεκτονική, preprocessing, features, loss functions και training protocol,
- datasets, splits, VRU classes, sensors και context,
- baselines, metrics, horizons, coordinate system και sampling rate,
- ακριβή αποτελέσματα με provenance σε σελίδα, πίνακα ή σχήμα,
- ablations, robustness, uncertainty και statistical significance,
- computational cost, κώδικα, checkpoints, licenses και reproducibility status,
- limitations, threats to validity και failure cases,
- IMPTC transfer plan και σαφή διάκριση μεταξύ author claims και thesis proposals.

## Κανόνες συγκρίσεων

ADE, FDE, minADE, minFDE, NLL και miss rate δεν συγκρίνονται αυτόματα όταν διαφέρουν:

- observation ή prediction horizon,
- sampling frequency,
- coordinate frame ή μονάδες,
- αριθμός samples/modes,
- dataset split,
- agent filtering,
- scene context,
- evaluation implementation.

Leaderboard δημιουργείται μόνο για protocol-compatible αποτελέσματα. Διαφορετικά, τα αποτελέσματα εμφανίζονται σε ξεχωριστές ομάδες και χαρακτηρίζονται ως μη άμεσα συγκρίσιμα.

## Quality gates

Κάθε paper λαμβάνει score 0–100 με βάση:

- evidence completeness,
- methodological depth,
- experimental rigor,
- reproducibility,
- dataset transparency,
- metric comparability,
- limitations και validity,
- transferability στο IMPTC.

Το evidence level περιορίζει το μέγιστο score. Ένα paper που αναλύθηκε μόνο από abstract δεν μπορεί να πάρει βαθμολογία επιπέδου full-text ή reproduced study.

## Παραγόμενα reports

Το `scripts/audit_research_quality.py` παράγει:

- `thesis/quality/research_quality_report.json`
- `thesis/quality/README.md`

Το report δείχνει quality grade, evidence level, ελλιπή πεδία, προτεραιότητα για full-text μελέτη και επιλεξιμότητα για leaderboard ή reproduction claim.

## Στόχος για το IMPTC

Η τελική πλατφόρμα πρέπει να καταλήγει σε τεκμηριωμένη research agenda:

1. ποια μοντέλα αποτελούν δίκαια baselines,
2. ποια δεδομένα IMPTC χρησιμοποιεί κάθε baseline,
3. ποια contextual modalities παραμένουν ανεκμετάλλευτα,
4. ποια experiments απομονώνουν traffic lights, weather, maps, camera και LiDAR,
5. ποια metrics μετρούν accuracy, uncertainty, safety και real-time feasibility,
6. ποια ερευνητικά gaps μπορούν να γίνουν πρωτότυπη συνεισφορά της διπλωματικής.

## Επόμενες ερευνητικές φάσεις

- full-text PDF ingestion με provenance ανά claim,
- structured result extraction και protocol-normalized benchmark groups,
- citation graph και genealogy μοντέλων,
- reproducibility registry για code, environment και checkpoints,
- IMPTC experiment registry με seeds, configs, runs και artifacts,
- systematic review flow συμβατό με PRISMA-style screening.

Η πλατφόρμα πρέπει να προτιμά την επιστημονική ακρίβεια από την πληρότητα: άγνωστα στοιχεία παραμένουν άγνωστα και δεν συμπληρώνονται με εικασίες.
