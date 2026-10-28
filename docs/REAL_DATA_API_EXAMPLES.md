# Public real-data API examples

Start the service with `uvicorn app.main:app --reload`.

## Dataset readiness and scope

```bash
curl http://127.0.0.1:8000/real-data/strategy
```

This reports whether the expected raw files and trained artifacts are present. It explicitly identifies the banking track as card fraud, not AML.

## Cryptocurrency graph

```bash
curl http://127.0.0.1:8000/real-data/elliptic/graph/123456
```

Requires `data/raw/elliptic/elliptic_txs_edgelist.csv`. The transaction ID is an example; use an ID from your downloaded dataset.

## Cryptocurrency score

```bash
curl http://127.0.0.1:8000/real-data/elliptic/score/123456
```

Requires the three Elliptic CSV files and a model trained with `python -m real_data.elliptic_pipeline`. The route currently scores source-labeled transactions only because it joins through the known-label dataset loader. A production inference path should be separated from the label table to avoid label availability assumptions.

## Banking card-fraud score

The feature names must match the trained artifact; send every required feature as a numeric value.

```bash
curl -X POST http://127.0.0.1:8000/real-data/banking/score \
  -H "Content-Type: application/json" \
  -d '{"features":{"Time":12345,"Amount":50,"V1":0.1,"V2":-0.2}}'
```

The abbreviated payload above will normally receive HTTP 422 because the full set of model features is required. Obtain the required feature list from `artifacts/banking_fraud_model.joblib` or use the dataset's row schema to build a complete request. Never use a card-fraud probability as an AML probability.
