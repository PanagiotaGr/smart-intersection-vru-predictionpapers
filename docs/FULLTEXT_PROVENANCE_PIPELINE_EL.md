# Full-text provenance pipeline

Το repository δεν θεωρεί πλέον ισοδύναμη μια ανάλυση abstract με μια πλήρη μελέτη paper. Η υποδομή αυτή ορίζει το ερευνητικό συμβόλαιο για εξαγωγή στοιχείων από πλήρες PDF, appendix, supplementary material και κώδικα.

## Βασική μονάδα: claim

Κάθε επιστημονικός ισχυρισμός αποθηκεύεται ως ανεξάρτητο claim με:

- μοναδικό `claim_id`
- κατηγορία claim
- ελληνική επιστημονική διατύπωση
- σελίδα και ενότητα
- table ή figure όταν υπάρχει
- τύπο πηγής
- confidence
- τρόπο εξαγωγής
- σαφή διάκριση `author_claim` και `thesis_inference`

## Ερευνητικές εγγυήσεις

1. Numerical result χωρίς page provenance δεν περνά validation.
2. Numerical result χωρίς table, figure ή section δεν θεωρείται κατάλληλο για synthesis.
3. Author claim και thesis inference δεν επιτρέπεται να είναι ταυτόχρονα αληθή.
4. Τα κενά στοιχεία παραμένουν null.
5. Η ύπαρξη PDF δεν σημαίνει ότι έχει ολοκληρωθεί full-text review.
6. Leaderboard επιτρέπεται μόνο όταν dataset, split, observation/prediction horizon, sampling rate, coordinate frame και metric definition είναι συμβατά.

## Αναμενόμενη είσοδος

Για κάθε paper μπορεί να δημιουργηθεί:

```text
data/fulltext_extractions/<paper_id>.json
```

Παράδειγμα:

```json
{
  "evidence_level": "full_text",
  "claims": [
    {
      "claim_type": "result",
      "claim_text_el": "Το μοντέλο παρουσιάζει χαμηλότερο minFDE στο συγκεκριμένο benchmark.",
      "source_kind": "table",
      "page": 8,
      "section": "4.2 Quantitative Results",
      "table": "Table 2",
      "figure": null,
      "quote_or_paraphrase": "paraphrase",
      "confidence": "high",
      "author_claim": true,
      "thesis_inference": false,
      "extraction_method": "manual_review"
    }
  ]
}
```

## Παραγόμενα αρχεία

```text
data/fulltext_research_records.json
data/fulltext_records/<paper_id>.json
thesis/quality/fulltext_provenance_report.json
```

## Επόμενα ερευνητικά στάδια

- αυτοματοποιημένο PDF text extraction με page boundaries
- structured table extraction
- equation and loss-function registry
- experiment protocol normalization
- code and checkpoint registry
- citation graph
- reproducibility manifests
- IMPTC experiment cards
- human-review queue για claims χαμηλού confidence

Η αυτοματοποίηση υποστηρίζει την έρευνα· δεν αντικαθιστά τον επιστημονικό έλεγχο του πλήρους paper.
