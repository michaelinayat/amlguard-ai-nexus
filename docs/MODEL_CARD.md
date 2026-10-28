# Model Card — AMLGuard AI Nexus Public-Data Pipelines

## Intended use

Research and professional-certification demonstration of ML-assisted risk triage, graph feature construction, and reproducible evaluation. Not a production AML decision system.

## Separate tasks

### Cryptocurrency
- Dataset: Elliptic Bitcoin transaction graph.
- Labels: source-provided licit, illicit, unknown. Unknown rows are excluded from supervised metrics but can be retained for inference.
- Graph: directed transaction-to-transaction edges, with in-degree and out-degree features.
- Split: time-aware train (steps <=34), validation (35–39), test (>=40).
- Metrics: precision, recall, F1, ROC-AUC, average precision/PR-AUC, confusion matrix, counts.
- Limitations: research labels are not legal proof; class imbalance is substantial; source-provided aggregated features may encode neighborhood information whose availability at scoring time must be audited.

### Banking/payment proxy
- Dataset: European Credit Card Fraud Detection.
- Labels: source-provided card fraud/non-fraud (`Class`).
- Task: card fraud classification, **not money-laundering detection**.
- Split: time-ordered 80/20 baseline using `Time` where available.
- Graph limitation: the dataset does not provide account identifiers for a transfer graph.
- Limitations: no claim of AML label validity or bank-account graph capability; license and source terms must be checked for the exact downloaded version.

## Data provenance and licensing

Raw data is not bundled. Record provider, version, date, SHA-256 checksums, exact license, and permitted research/training/model-sharing/redistribution/commercial uses in `DATASET_MANIFEST_TEMPLATE.json`. Public accessibility alone does not grant redistribution or commercial rights.

## Traditional bank AML gap

This release does not claim a verified public non-synthetic traditional-bank dataset with investigator-confirmed AML labels. The card-fraud dataset is an adjacent banking risk task and cannot substitute for AML ground truth. A true bank AML track needs authorized data and documented outcome labels.

## Responsible use

Scores are triage signals only. They must not independently trigger account closure, freezing, denial of service, or allegations. Require human review, independent validation, privacy/legal review, model risk governance, monitoring, and drift/fairness assessment before operational use.
