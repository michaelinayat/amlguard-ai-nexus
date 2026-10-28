# AMLGuard AI Nexus — Public Real-Data Strategy

## Executive decision

Use two separately governed datasets and two separately named modeling tasks. The cryptocurrency track uses the public Elliptic Bitcoin transaction graph with source-provided licit/illicit/unknown labels. The banking track uses the public European Credit Card Fraud Detection dataset as a **card-fraud proxy**, not as an AML-labelled dataset. This satisfies the requirement for public, non-synthetic source data with existing labels for both tracks, while making the important limitation explicit: the banking labels are fraud labels, not money-laundering findings.

There is no verified, openly redistributable, non-synthetic, labeled traditional-bank AML transaction dataset in this package. Research literature explains that bank transaction confidentiality is a key reason real bank AML datasets are not publicly available. Do not relabel card fraud as AML. A true bank AML supervised track requires an authorized bank/research partner dataset with investigator-reviewed outcomes and permission to use it.

## Dataset registry and license diligence

### A. Cryptocurrency — Elliptic Bitcoin Dataset

- Primary description/download page: https://www.kaggle.com/datasets/ellipticco/elliptic-data-set
- Research paper: Weber et al., *Anti-Money Laundering in Bitcoin: Experimenting with Graph Convolutional Networks for Financial Forensics*, KDD 2019 workshop, https://arxiv.org/abs/1908.02591
- Public mirrors/documentation: https://huggingface.co/datasets/edisonlin2002/elliptic-bitcoin-dataset
- Data: transaction feature table, source labels, and directed transaction-to-transaction edge list. Commonly reported scale is 203,769 transactions and 234,355 edges; 4,545 labeled illicit, 42,019 labeled licit, and 157,205 unknown. Confirm counts against the exact downloaded version.
- Labels: source label `1` = illicit, `2` = licit, `unknown` = no supervised label. These are research labels, not legal proof and not exhaustive ground truth.
- License: verify the current license and terms on the exact provider/version before redistribution or commercial use. This project does not bundle or redistribute the raw data. Cite the original paper and dataset provider.
- Graph: each transaction is a node; each directed edge represents a transaction-flow relationship as defined by the dataset.

### B. Banking/payment — European Credit Card Fraud Detection

- Provider page: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
- Data description: anonymized card transactions, with `Class` labels (`1` fraud, `0` non-fraud); features include `Time`, `Amount`, and anonymized PCA-derived `V1`–`V28`.
- Use: labeled payment-card fraud classification as an adjacent banking risk task. It is **not labeled for money laundering** and must not be reported as an AML model result.
- License: public access does not itself establish redistribution/commercial permission. Review the exact current provider terms and record the version and license in the submission before use. Raw data is not bundled.
- Graph limitation: this dataset does not provide account/merchant identifiers needed to construct an account-transfer graph. The graph builder in this repository only runs when the chosen banking dataset has genuine source/destination entity columns; it deliberately refuses to invent them.

### Optional real banking data for graph exploration — MoneyData

- Dataset record: https://data.mendeley.com/datasets/dnxtg6n4rv/1
- Public metadata describes anonymized real-world retail bank transactions spanning seven years and identifies CC BY 4.0. Review the exact record and schema before use.
- It may support descriptive transaction-network analysis if account/relationship identifiers are included in the actual downloadable version. Its categories are not verified AML investigation outcomes; therefore it is not a supervised AML label source unless the actual schema and provenance prove otherwise.

## Acquisition and file layout

Do not check raw datasets into Git or include them in the submission ZIP. Download from the provider under its current terms and place the files locally:

```text
data/raw/
  elliptic/
    elliptic_txs_features.csv
    elliptic_txs_classes.csv
    elliptic_txs_edgelist.csv
  banking/
    creditcard.csv
```

Then run:

```bash
python -m real_data.elliptic_pipeline
python -m real_data.banking_pipeline
```

Artifacts and evaluation reports are written to `artifacts/`. If the files are absent, the pipeline exits with a clear message; it never creates fake labels or silently falls back to synthetic data.

## Preprocessing and label handling

### Elliptic

1. Read feature, label, and edge files independently and join on the transaction ID.
2. Normalize source labels; retain only known `1`/`2` labels for supervised fitting and metrics. Keep unknown rows out of supervised evaluation.
3. Convert positional feature columns to numeric values; treat infinities as missing; impute medians inside the model pipeline.
4. Build a directed NetworkX graph from the supplied edge list. Add in-degree and out-degree as explicit, inspectable graph features.
5. Split by `time_step`: train `<=34`, validation `35–39`, test `>=40`. Do not randomly shuffle the temporal dataset. Use validation only for model/threshold selection; report final metrics on the later test period.
6. Use class weighting; report precision, recall, F1, ROC-AUC, average precision/PR-AUC, confusion matrix, support and class prevalence. Accuracy alone is insufficient for rare illicit labels.

**Leakage note:** Elliptic includes aggregated neighbor features in its source feature table. Their construction and temporal availability should be documented; do not describe this baseline as a strict real-time deployment evaluation without verifying feature availability at prediction time.

### Banking card-fraud proxy

1. Require an existing `Class` label column. Reject data without both classes rather than inventing labels.
2. Parse numeric columns and replace infinite values with missing values.
3. Sort by `Time` and use the first 80% for training and last 20% for test as a baseline. Check that both classes appear in both partitions; if not, investigate the data version and use a justified time-aware split rather than silently randomizing.
4. Fit a class-weighted Random Forest in a pipeline; report precision, recall, F1, ROC-AUC, average precision/PR-AUC, confusion matrix and counts.
5. Clearly label all output as **card-fraud**. Do not call its probability an AML probability.

## Graph construction

- Elliptic: node = transaction, directed edge = transaction flow in source edge list; compute in-degree/out-degree. `GET /real-data/elliptic/graph/{tx_id}` exposes degree and a capped sample of neighbors when raw edges are installed.
- Banking: the credit-card dataset has no account-level IDs, so no account-transfer graph can be truthfully built from it. `scripts/real_data/build_transaction_graph.py` builds a graph only from a separate CSV that genuinely contains source/destination account identifiers. It fails fast if they are missing.
- Graph signals describe relationships, not criminal intent. Shared service nodes, exchanges, and high-degree nodes can create false positives.

## API changes

- `GET /real-data/strategy`: dataset readiness, tasks, graph capability and limitations.
- `GET /real-data/elliptic/graph/{tx_id}`: graph neighborhood summary; returns `503` until edge data is installed.
- `GET /real-data/elliptic/score/{tx_id}`: model score for a source-labeled Elliptic transaction; requires a trained artifact.
- `POST /real-data/banking/score`: takes a dictionary of feature values matching the trained card-fraud model; returns a **card-fraud proxy** score only.
- Existing `/score` and `/dataset/summary` endpoints remain for backward compatibility with the original synthetic demo. They are explicitly marked as legacy and must not be used as evidence of real-data model performance.

## License and reproducibility checklist

- [ ] Record exact provider URL, download date, dataset version, file checksums and license text in the submission.
- [ ] Confirm training, derivative-model, redistribution and commercial-use rights for the exact files.
- [ ] Do not redistribute raw datasets unless the license explicitly permits it.
- [ ] Cite Elliptic and its original paper; cite the banking dataset provider.
- [ ] Store raw data locally under `data/raw/`, excluded from source-control and the deliverable ZIP.
- [ ] Save code version, package versions, split boundaries, seed, model parameters, and evaluation JSON.
- [ ] Do not claim real-bank AML validation from card-fraud labels or cryptocurrency research labels.

## Responsible use and certification claims

This is a research prototype, not a production AML decision system. Scores prioritize human review; they do not establish guilt, trigger automatic account restrictions, or replace an institution's AML program. Labels are incomplete and may reflect investigator or provider coverage. Evaluation is dataset-specific and may not transfer to other populations, products, jurisdictions, or time periods. Before production use, require legal/privacy review, model risk management, drift monitoring, independent validation, explainability review, secure data controls, and documented investigator feedback.
