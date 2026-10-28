from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from real_data.api import router as real_data_router
from app.workspace import router as workspace_router

app = FastAPI(
    title="AMLGuard AI Nexus",
    version="2.0.0",
    description=(
        "Public-data research prototype with separate Elliptic cryptocurrency and "
        "non-synthetic card-fraud banking-proxy pipelines. No synthetic data is used "
        "by the active scoring routes. Banking card-fraud labels are not AML labels."
    ),
)
app.include_router(real_data_router)
app.include_router(workspace_router)

@app.get("/")
def root():
    return {
        "service": "AMLGuard AI Nexus",
        "status": "running",
        "mode": "public-data adapters; raw datasets and trained real-data models are not bundled",
        "active_scoring": "Use /real-data routes after obtaining data and training models",
        "legacy_demo": "Synthetic-data routes are disabled in this release",
        "warning": "Research scores are triage signals, not proof of criminal activity.",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dataset/summary")
def legacy_dataset_summary():
    raise HTTPException(status_code=410, detail="Legacy synthetic dataset endpoint disabled. Use GET /real-data/strategy.")

@app.get("/graph/account/{account_id}")
def legacy_account_graph(account_id: str):
    raise HTTPException(status_code=410, detail="Legacy synthetic account graph disabled. Use GET /real-data/elliptic/graph/{tx_id} after installing the public dataset.")

@app.post("/score")
def legacy_score():
    raise HTTPException(status_code=410, detail="Legacy synthetic scoring endpoint disabled. Use /real-data/elliptic/score/{tx_id} or /real-data/banking/score after training the appropriate model.")

# Static frontend is available at /ui; API and Swagger routes remain unchanged.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
