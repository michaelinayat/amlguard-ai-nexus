# Implementation Roadmap — Public Real-Data Edition

| Phase | Workstream | Implementation | Acceptance evidence |
|---|---|---|---|
| 1 | Dataset governance | Dataset registry, source URLs, label definitions, license checklist and manifest template | `REAL_DATA_STRATEGY.md`, `DATASET_MANIFEST_TEMPLATE.json` |
| 2 | Cryptocurrency data | Elliptic loader, label normalization, directed graph construction and graph degree features | `real_data/elliptic_pipeline.py` |
| 3 | Banking/payment data | Existing card-fraud labels, numeric preprocessing, time-ordered train/test split | `real_data/banking_pipeline.py` |
| 4 | ML training | Class-weighted Random Forest baselines, imputation pipelines and model artifacts | Dataset-specific evaluation JSON generated after data acquisition |
| 5 | Evaluation | Precision, recall, F1, ROC-AUC, average precision/PR-AUC, confusion matrix, class counts | `artifacts/*_evaluation.json` (generated locally) |
| 6 | API | Readiness endpoint, Elliptic graph/score endpoints, card-fraud score endpoint | `/real-data/*` routes |
| 7 | Graph interoperability | Graph builder only when genuine account/source/destination identifiers exist | `scripts/real_data/build_transaction_graph.py` |
| 8 | Testing | API, label integrity, graph schema and scope tests | `PYTHONPATH=. pytest -q` |
| 9 | Governance | Human review, license diligence, no automated adverse action, no cross-domain label conflation | `MODEL_CARD.md`, `RISK_REGISTER.md` |

## Status

Code and tests are implemented. Actual model training/evaluation remains pending until the user obtains the raw public datasets and verifies their terms. The project does not include synthetic fallback data and does not fabricate labels. The banking track is card-fraud proxy work, not a verified AML classifier.
