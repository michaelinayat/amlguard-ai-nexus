# Certification Demo Checklist — Public Real-Data Edition

## Before demo
- [ ] Review current dataset license/terms for the exact provider/version.
- [ ] Download raw Elliptic files into `data/raw/elliptic/` (not included in the project ZIP).
- [ ] Download the public European Credit Card Fraud Detection CSV into `data/raw/banking/` (not included in the project ZIP).
- [ ] Fill in `DATASET_MANIFEST_TEMPLATE.json` with source, date, version, checksums and verified permissions.
- [ ] Run `python -m real_data.elliptic_pipeline` and archive the generated evaluation JSON.
- [ ] Run `python -m real_data.banking_pipeline` and archive the generated evaluation JSON.
- [ ] Run `PYTHONPATH=. pytest -q`.
- [ ] Start API and check `/real-data/strategy`.

## Suggested 5-minute narrative
1. Explain why the cryptocurrency and banking tracks are separate.
2. Demonstrate Elliptic graph nodes/edges and its source-provided labels.
3. Show time-aware evaluation and PR-AUC/recall under class imbalance.
4. Show card-fraud proxy pipeline and explicitly state that its labels are not AML labels.
5. Show API status and human-review safeguards.
6. Discuss license diligence, unknown labels, graph limitations and the need for authorized true bank AML data.

## Honest reporting
- Do not report results until the actual public datasets are downloaded and pipelines run.
- Do not present historical synthetic-demo screenshots/metrics as results from the public-data edition.
- Do not claim the banking track detects money laundering.
