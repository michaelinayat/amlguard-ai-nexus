"""Optional FastAPI router for real-data model endpoints; raw datasets are never bundled."""
from pathlib import Path
import pandas as pd
import joblib
import networkx as nx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .elliptic_pipeline import ROOT, RAW as ELLIPTIC_RAW, load_elliptic
from .banking_pipeline import DEFAULT_CSV as BANKING_CSV

router = APIRouter(prefix="/real-data", tags=["real-data"])
ELLIPTIC_MODEL = ROOT / "artifacts" / "elliptic_model.joblib"
BANKING_MODEL = ROOT / "artifacts" / "banking_fraud_model.joblib"

class BankingScoreRequest(BaseModel):
    features: dict[str, float] = Field(..., description="Feature names and values matching the trained banking model artifact")

@router.get("/strategy")
def real_data_strategy():
    return {
      "mode": "public-real-data adapters; no raw dataset is bundled",
      "cryptocurrency": {"dataset": "Elliptic Bitcoin transaction graph", "status": "ready_to_ingest" if all((ELLIPTIC_RAW / f).exists() for f in ("elliptic_txs_features.csv", "elliptic_txs_classes.csv", "elliptic_txs_edgelist.csv")) else "awaiting_user_download", "task": "research-labeled illicit-vs-licit transaction classification", "graph": "directed transaction-to-transaction edges"},
      "banking": {"dataset": "European Credit Card Fraud Detection", "status": "ready_to_ingest" if BANKING_CSV.exists() else "awaiting_user_download", "task": "card-fraud proxy, not AML", "graph": "not available from this dataset because account/merchant relationship IDs are not provided"},
      "label_policy": "Do not create or infer ground-truth labels. Unknown labels are excluded from supervised metrics.",
      "license_policy": "Review the exact provider and version terms before training, sharing, or commercial deployment."
    }

@router.get("/elliptic/graph/{tx_id}")
def elliptic_graph(tx_id: str):
    edge_path = ELLIPTIC_RAW / "elliptic_txs_edgelist.csv"
    if not edge_path.exists():
        raise HTTPException(status_code=503, detail="Elliptic edge list not installed. Follow docs/REAL_DATA_STRATEGY.md.")
    edges = pd.read_csv(edge_path)
    edges = edges.iloc[:, :2].copy(); edges.columns = ["src", "dst"]
    edges = edges.astype(str)
    g = nx.DiGraph(); g.add_edges_from(edges.itertuples(index=False, name=None))
    if tx_id not in g:
        raise HTTPException(status_code=404, detail="Transaction ID is not present in the loaded edge list.")
    return {"transaction_id": tx_id, "in_degree": int(g.in_degree(tx_id)), "out_degree": int(g.out_degree(tx_id)),
            "incoming_neighbors_sample": list(g.predecessors(tx_id))[:20], "outgoing_neighbors_sample": list(g.successors(tx_id))[:20],
            "interpretation": "Graph relationships are investigative context, not proof of criminal activity."}

@router.get("/elliptic/score/{tx_id}")
def score_elliptic(tx_id: str):
    if not ELLIPTIC_MODEL.exists():
        raise HTTPException(status_code=503, detail="Elliptic model not trained. Run python -m real_data.elliptic_pipeline after obtaining the dataset.")
    try:
        df, _ = load_elliptic(include_unknown=True)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    row = df[df.txId.astype(str) == str(tx_id)]
    if row.empty:
        raise HTTPException(status_code=404, detail="Transaction ID is not present in the loaded feature data.")
    artifact = joblib.load(ELLIPTIC_MODEL)
    features = artifact["features"]
    prob = float(artifact["model"].predict_proba(row[features])[0, 1])
    return {"transaction_id": tx_id, "dataset": "Elliptic", "model_probability_for_source_illicit_label": round(prob, 6),
            "risk_band": "HIGH" if prob >= .7 else "MEDIUM" if prob >= .4 else "LOW",
            "source_label": str(row.iloc[0]["label"]), "human_review_required": True,
            "disclaimer": "Research model output only. Labels and scores are not proof of criminal activity."}

@router.post("/banking/score")
def score_banking(req: BankingScoreRequest):
    if not BANKING_MODEL.exists():
        raise HTTPException(status_code=503, detail="Banking fraud model not trained. See docs/REAL_DATA_STRATEGY.md.")
    artifact = joblib.load(BANKING_MODEL)
    features = artifact["features"]
    missing = [f for f in features if f not in req.features]
    if missing:
        raise HTTPException(status_code=422, detail={"missing_features": missing})
    X = pd.DataFrame([{f: req.features[f] for f in features}], columns=features)
    prob = float(artifact["model"].predict_proba(X)[0, 1])
    return {"dataset": "European Credit Card Fraud Detection", "task": "card fraud proxy, not AML", "model_probability_for_card_fraud_label": round(prob, 6),
            "risk_band": "HIGH" if prob >= .7 else "MEDIUM" if prob >= .4 else "LOW", "human_review_required": True,
            "disclaimer": "Card-fraud research model, not an AML model. Do not use as a standalone decision."}
