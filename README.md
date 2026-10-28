# AMLGuard AI Nexus — Public Real-Data Edition

Advanced certification project demonstrating separate cryptocurrency transaction graph analytics and a labeled banking/payment fraud research pipeline. The active application does **not** use synthetic accounts, synthetic transactions, or synthetic labels. Raw datasets and trained models are intentionally not included; download them from their providers after reviewing the current terms.

## Scope and honest claims

- **Cryptocurrency:** Elliptic Bitcoin transaction graph with source-provided licit/illicit/unknown labels. This is a research benchmark; labels are not legal proof.
- **Banking/payment:** European Credit Card Fraud Detection, with source-provided fraud/non-fraud labels. This is a non-synthetic card-fraud proxy, **not an AML-labeled dataset**.
- **Traditional bank AML gap:** This package does not claim to have verified public non-synthetic bank transactions with investigator-confirmed laundering labels. That requires authorized partner data.
- **Graph:** A transaction graph is built for Elliptic from its edge list. A generic banking account graph builder works only when the chosen source genuinely provides source/destination entity IDs; the card-fraud dataset does not.

See [the complete data strategy](docs/REAL_DATA_STRATEGY.md) for data sources, label definitions, license diligence, preprocessing, graph construction, evaluation, API routes and limitations.

## Install

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Obtain datasets

Review the provider's current license and use conditions first. The raw files must be placed locally as follows:

```text
data/raw/
  elliptic/
    elliptic_txs_features.csv
    elliptic_txs_classes.csv
    elliptic_txs_edgelist.csv
  banking/
    creditcard.csv
```

The project does not redistribute those files. Record source, version, download date, checksums, and permitted use in `docs/DATASET_MANIFEST_TEMPLATE.json`.

## Train and evaluate

```bash
python -m real_data.elliptic_pipeline
python -m real_data.banking_pipeline
```

Outputs are written under `artifacts/`:
- `elliptic_model.joblib` and `elliptic_evaluation.json`
- `banking_fraud_model.joblib` and `banking_fraud_evaluation.json`

Elliptic uses a time-aware split (train steps <=34, validation 35–39, test >=40) and excludes unknown labels from supervised metrics. The banking baseline sorts by `Time` and uses the first 80% for training and the last 20% for testing. Both report precision, recall, F1, ROC-AUC, average precision/PR-AUC, confusion matrix, and sample counts. The split and thresholds are research baselines and require validation before any operational use.

## Run the API

```bash
uvicorn app.main:app --reload
```

- `GET /health`
- `GET /real-data/strategy`
- `GET /real-data/elliptic/graph/{tx_id}`
- `GET /real-data/elliptic/score/{tx_id}`
- `POST /real-data/banking/score`

Examples: [docs/REAL_DATA_API_EXAMPLES.md](docs/REAL_DATA_API_EXAMPLES.md). The old synthetic `/score`, `/dataset/summary`, and `/graph/account/{account_id}` endpoints return HTTP 410 and are disabled.

## Graph construction for a real banking dataset

If an authorized or public non-synthetic banking CSV contains actual entity columns, run:

```bash
python scripts/real_data/build_transaction_graph.py your_transactions.csv --source-col source_account --destination-col destination_account --amount-col amount
```

The script refuses to build a graph if source/destination entity IDs are missing; it does not fabricate accounts or edges.

## Tests

```bash
PYTHONPATH=. pytest -q
python -m py_compile app/main.py real_data/*.py scripts/real_data/*.py tests/*.py
```

## Responsible use

All scores are research triage signals and require human review. Do not automatically freeze accounts, deny services, or make adverse decisions from model output. Public labels may be incomplete or biased. A card-fraud score is not an AML score; cryptocurrency results do not automatically generalize to traditional banking. Review privacy, licensing, model risk, fairness, drift, and feature availability before any production deployment.

## Full local web application

The responsive browser app is served by the same FastAPI backend. It includes:

- Overview dashboard and live data/model readiness checks.
- Elliptic cryptocurrency transaction scoring and directed graph-neighborhood investigation.
- Card-fraud feature scoring, explicitly distinguished from AML detection.
- Persistent alert queue. A score can be saved as an alert only after the real-data API returns a valid score; provenance is required. No sample alerts are seeded.
- Investigation case register with status and priority tracking.
- Reports with CSV/JSON workspace exports and visibility into evaluation JSON files produced by real training runs.
- SQLite persistence at `data/workspace.db` for analyst cases and saved alerts. Do not put sensitive customer information in this local research app.

### Windows quick start

1. Install Python 3.11 or 3.12.
2. Extract the ZIP and open the project root (the folder containing `requirements.txt`).
3. Double-click `run_windows.bat`, or run:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```
4. Open **http://127.0.0.1:8000/ui**. API documentation is at **http://127.0.0.1:8000/docs**.
5. Run `test_windows.bat` or execute ` .\.venv\Scripts\python.exe -m pytest -q` to run tests.

### Workspace API

- `GET /workspace/summary`
- `GET|POST /workspace/cases`; `PATCH /workspace/cases/{case_id}`
- `GET|POST /workspace/alerts`; `PATCH /workspace/alerts/{alert_id}`
- `GET /workspace/reports/summary`
- `GET /workspace/reports/evaluations`
- `GET /workspace/reports/export.csv`
- `GET /workspace/reports/export.json`

The workspace starts empty by design. Cases are analyst-entered; alerts must include score provenance. Reports include only persisted records and actual evaluation artifacts, not invented activity. The browser UI is in `frontend/` and mounted at `/ui`.

### Data and model readiness

Raw datasets and trained models are not bundled. Place source files in `data/raw/` and run `python -m real_data.elliptic_pipeline` and/or `python -m real_data.banking_pipeline` before scoring. If files/models are absent, scoring endpoints return a setup error instead of a fabricated prediction. The European card-fraud dataset is not an AML-labeled dataset; cryptocurrency research outputs do not prove criminality or generalize automatically to traditional banking.
