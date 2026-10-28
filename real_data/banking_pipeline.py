"""Preprocess and train on a public, non-synthetic labeled card-fraud dataset.

Expected CSV: European Credit Card Fraud Detection (Kaggle), with `Time`, `Amount`,
V1..V28, and `Class` (1=fraud, 0=non-fraud). This is a banking/card-fraud proxy,
NOT an AML-labeled dataset. It does not contain account identifiers for a transaction graph.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "raw" / "banking" / "creditcard.csv"
MODEL_OUT = ROOT / "artifacts" / "banking_fraud_model.joblib"
REPORT_OUT = ROOT / "artifacts" / "banking_fraud_evaluation.json"

def load_banking(csv_path: Path) -> tuple[pd.DataFrame, list[str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}. Obtain the public European Credit Card Fraud Detection dataset via its provider and review current terms; see docs/REAL_DATA_STRATEGY.md.")
    df = pd.read_csv(csv_path)
    if "Class" not in df.columns:
        raise ValueError("Expected a 'Class' label column (1=fraud, 0=non-fraud). No labels are fabricated.")
    df["Class"] = pd.to_numeric(df["Class"], errors="coerce")
    df = df[df["Class"].isin([0, 1])].copy()
    target = "Class"
    features = [c for c in df.columns if c != target]
    for c in features:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan)
    if df.empty or df[target].nunique() != 2:
        raise ValueError("Expected both fraud and non-fraud labels after cleaning.")
    return df, features

def train(csv_path: Path = DEFAULT_CSV, model_out: Path = MODEL_OUT, report_out: Path = REPORT_OUT) -> dict:
    df, features = load_banking(csv_path)
    # Dataset `Time` is elapsed time, not a calendar timestamp. Sort chronologically where available.
    if "Time" in df.columns:
        df = df.sort_values("Time", kind="stable")
    cut = int(len(df) * 0.8)
    train_df, test_df = df.iloc[:cut], df.iloc[cut:]
    if train_df.Class.nunique() != 2 or test_df.Class.nunique() != 2:
        raise ValueError("Chronological split lacks both classes. Inspect dataset version and split; do not silently randomize.")
    model = Pipeline([("imputer", SimpleImputer(strategy="median")),
        ("classifier", RandomForestClassifier(n_estimators=250, max_depth=12,
          class_weight="balanced_subsample", random_state=42, n_jobs=-1))])
    model.fit(train_df[features], train_df.Class)
    prob = model.predict_proba(test_df[features])[:, 1]
    pred = (prob >= 0.5).astype(int)
    metrics = {"dataset": "European Credit Card Fraud Detection", "task": "card fraud vs non-fraud (not AML)",
      "split": "first 80% train, last 20% test after sorting by Time", "counts": {"rows": int(len(df)), "train": int(len(train_df)), "test": int(len(test_df)), "test_fraud": int(test_df.Class.sum())},
      "metrics": {"precision": float(precision_score(test_df.Class, pred, zero_division=0)), "recall": float(recall_score(test_df.Class, pred, zero_division=0)),
        "f1": float(f1_score(test_df.Class, pred, zero_division=0)), "roc_auc": float(roc_auc_score(test_df.Class, prob)), "average_precision_pr_auc": float(average_precision_score(test_df.Class, prob))},
      "classification_report": classification_report(test_df.Class, pred, output_dict=True, zero_division=0), "confusion_matrix": confusion_matrix(test_df.Class, pred).tolist(),
      "limitations": ["This is labeled payment-card fraud, not money laundering.", "No account IDs are provided, so an account-transfer graph cannot be built from this dataset alone.",
        "Source availability does not guarantee redistribution or commercial rights; review the provider's current terms.", "Threshold 0.5 is a baseline and needs validation for operational costs."]}
    model_out.parent.mkdir(parents=True, exist_ok=True); report_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": features, "dataset": "banking_card_fraud", "target": "Class"}, model_out)
    report_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2)); print(f"Saved model: {model_out}\nSaved evaluation: {report_out}")
    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--csv", type=Path, default=DEFAULT_CSV); parser.add_argument("--model-out", type=Path, default=MODEL_OUT); parser.add_argument("--report-out", type=Path, default=REPORT_OUT)
    a = parser.parse_args(); train(a.csv, a.model_out, a.report_out)
