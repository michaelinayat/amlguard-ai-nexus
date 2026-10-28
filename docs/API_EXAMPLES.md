# API Examples — Public Real-Data Edition

Start with `uvicorn app.main:app --reload`.

- `GET /health` — service health.
- `GET /real-data/strategy` — dataset readiness, label/task scope, and graph capability.
- `GET /real-data/elliptic/graph/{tx_id}` — directed transaction graph degree and neighbor sample; requires Elliptic edge list.
- `GET /real-data/elliptic/score/{tx_id}` — Elliptic research-model probability; requires raw data and trained artifact.
- `POST /real-data/banking/score` — card-fraud proxy probability; requires trained artifact and every numeric feature in the artifact.

Legacy synthetic endpoints `/score`, `/dataset/summary`, and `/graph/account/{account_id}` are disabled and return HTTP 410.

For exact request examples and limitations, see `REAL_DATA_API_EXAMPLES.md`. Never call card-fraud probability an AML probability.
