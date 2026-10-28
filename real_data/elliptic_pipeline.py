"""Preprocess and train on the public Elliptic Bitcoin research dataset.

Expected files (obtain from the official/research distribution; do not commit raw data):
  elliptic_txs_features.csv, elliptic_txs_classes.csv, elliptic_txs_edgelist.csv
The raw Elliptic labels are research labels, not court-proven findings.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (average_precision_score, classification_report,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "elliptic"
OUT = ROOT / "artifacts" / "elliptic_model.joblib"
REPORT = ROOT / "artifacts" / "elliptic_evaluation.json"
FILES = ("elliptic_txs_features.csv", "elliptic_txs_classes.csv", "elliptic_txs_edgelist.csv")


def load_elliptic(raw_dir: Path = RAW, include_unknown: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = [f for f in FILES if not (raw_dir / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing Elliptic files in {raw_dir}: {', '.join(missing)}. See docs/REAL_DATA_STRATEGY.md.")
    features = pd.read_csv(raw_dir / FILES[0], header=None)
    # Original release: txId, time_step, then 165 positional features; some mirrors include headers.
    if str(features.iloc[0, 0]).lower() in {"txid", "tx_id"}:
        features = pd.read_csv(raw_dir / FILES[0])
        features.columns = [str(c) for c in features.columns]
        id_col = next(c for c in features.columns if c.lower() in {"txid", "tx_id"})
        time_col = next(c for c in features.columns if c.lower() in {"time_step", "timestep", "time step"})
        features = features.rename(columns={id_col: "txId", time_col: "time_step"})
    else:
        features = features.rename(columns={0: "txId", 1: "time_step"})
        features.columns = ["txId", "time_step"] + [f"f{i:03d}" for i in range(features.shape[1] - 2)]
    classes = pd.read_csv(raw_dir / FILES[1])
    classes.columns = [str(c) for c in classes.columns]
    id_col = next(c for c in classes.columns if c.lower() in {"txid", "tx_id"})
    label_col = next(c for c in classes.columns if c.lower() in {"class", "label", "labels"})
    classes = classes.rename(columns={id_col: "txId", label_col: "label"})[["txId", "label"]]
    edges = pd.read_csv(raw_dir / FILES[2], header=None)
    if len(edges) and any(str(v).strip().lower() in {"txid1", "src", "source", "source_tx", "tx_id_1"} for v in edges.iloc[0, :2]):
        edges = edges.iloc[1:].reset_index(drop=True)
    if edges.shape[1] < 2:
        raise ValueError("Elliptic edge list must have two columns.")
    edges = edges.iloc[:, :2].copy()
    edges.columns = ["src", "dst"]
    graph = nx.DiGraph()
    graph.add_edges_from(edges.astype(str).itertuples(index=False, name=None))
    graph_features = pd.DataFrame({
        "txId": list(graph.nodes),
        "graph_in_degree": [graph.in_degree(n) for n in graph.nodes],
        "graph_out_degree": [graph.out_degree(n) for n in graph.nodes],
    })
    df = features.merge(classes, on="txId", how="left").merge(graph_features, on="txId", how="left")
    df["graph_in_degree"] = df["graph_in_degree"].fillna(0)
    df["graph_out_degree"] = df["graph_out_degree"].fillna(0)
    df["label_text"] = df["label"].astype(str).str.strip().str.lower()
    # Known labels only for training by default. In inference mode retain unknown rows
    # but never invent a target label for them.
    known = df["label_text"].isin({"1", "2", "illicit", "licit"})
    if not include_unknown:
        df = df[known].copy()
        df["target_illicit"] = df["label_text"].isin({"1", "illicit"}).astype(int)
    else:
        df["target_illicit"] = np.where(known, df["label_text"].isin({"1", "illicit"}).astype(int), np.nan)
    numeric = [c for c in df.columns if c not in {"txId", "label", "label_text", "target_illicit"}]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan)
    return df, pd.DataFrame({"feature": numeric})


def train(raw_dir: Path = RAW, out_path: Path = OUT, report_path: Path = REPORT) -> dict:
    df, _ = load_elliptic(raw_dir)
    if "time_step" not in df:
        raise ValueError("Elliptic time_step column was not identified.")
    # Chronological split avoids random shuffling across time. Keep only labeled rows for metrics.
    train_df = df[df.time_step <= 34]
    val_df = df[(df.time_step >= 35) & (df.time_step <= 39)]
    test_df = df[df.time_step >= 40]
    if min(len(train_df), len(val_df), len(test_df)) == 0:
        raise ValueError("Temporal split produced an empty partition; check dataset time_step parsing.")
    excluded = {"txId", "label", "label_text", "target_illicit"}
    features = [c for c in df.columns if c not in excluded]
    X_train, y_train = train_df[features], train_df.target_illicit
    X_test, y_test = test_df[features], test_df.target_illicit
    model = Pipeline([("imputer", SimpleImputer(strategy="median")),
        ("classifier", RandomForestClassifier(n_estimators=250, max_depth=12,
          class_weight="balanced_subsample", random_state=42, n_jobs=-1))])
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.5).astype(int)
    metrics = {
        "dataset": "Elliptic Bitcoin transaction graph",
        "task": "illicit-vs-licit among source-labeled transactions",
        "split": {"train_time_steps": "<=34", "validation_time_steps": "35-39 (reserved; threshold tuning not automated)", "test_time_steps": ">=40"},
        "counts": {"train_labeled": int(len(train_df)), "validation_labeled": int(len(val_df)), "test_labeled": int(len(test_df)),
                   "test_positive": int(y_test.sum()), "test_negative": int((y_test == 0).sum())},
        "metrics": {"precision": float(precision_score(y_test, pred, zero_division=0)),
                    "recall": float(recall_score(y_test, pred, zero_division=0)),
                    "f1": float(f1_score(y_test, pred, zero_division=0)),
                    "roc_auc": float(roc_auc_score(y_test, prob)) if y_test.nunique() == 2 else None,
                    "average_precision_pr_auc": float(average_precision_score(y_test, prob)) if y_test.nunique() == 2 else None},
        "classification_report": classification_report(y_test, pred, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "limitations": ["Research labels are not legal proof of crime.", "Unknown-label rows are excluded from supervised metrics.",
                        "Original aggregated features may encode neighbor information; document this when interpreting temporal results.",
                        "Threshold 0.5 is a baseline and should be tuned on validation data for the use case."]
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": features, "dataset": "elliptic", "label_mapping": {"1": 1, "2": 0}}, out_path)
    report_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"Saved model: {out_path}\nSaved evaluation: {report_path}")
    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    parser.add_argument("--model-out", type=Path, default=OUT)
    parser.add_argument("--report-out", type=Path, default=REPORT)
    args = parser.parse_args()
    train(args.raw_dir, args.model_out, args.report_out)
