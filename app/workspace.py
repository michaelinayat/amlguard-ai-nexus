"""Persistent investigation workspace: analyst-entered cases and score-backed alerts.

This module never invents transactions, labels, or model scores. Alerts can only be
created from a response supplied by the UI after a real-data scoring request, or from
an explicitly analyst-created note with provenance recorded.
"""
from __future__ import annotations
import csv
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "workspace.db"
router = APIRouter(prefix="/workspace", tags=["investigation-workspace"])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db() -> None:
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            dataset TEXT NOT NULL,
            entity_ref TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'open',
            summary TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            dataset TEXT NOT NULL,
            entity_ref TEXT NOT NULL,
            risk_band TEXT NOT NULL,
            score REAL NOT NULL,
            score_type TEXT NOT NULL,
            source_label TEXT NOT NULL DEFAULT 'not provided',
            provenance TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            case_id INTEGER,
            FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE SET NULL
        );
        """)


class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    dataset: str = Field(pattern=r"^(elliptic|card_fraud|other)$")
    entity_ref: str = Field(min_length=1, max_length=160)
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    summary: str = Field(default="", max_length=4000)

class CasePatch(BaseModel):
    status: Optional[str] = Field(default=None, pattern=r"^(open|in_review|closed)$")
    priority: Optional[str] = Field(default=None, pattern=r"^(low|medium|high|critical)$")
    summary: Optional[str] = Field(default=None, max_length=4000)

class AlertCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    dataset: str = Field(pattern=r"^(elliptic|card_fraud)$")
    entity_ref: str = Field(min_length=1, max_length=160)
    risk_band: str = Field(pattern=r"^(LOW|MEDIUM|HIGH)$")
    score: float = Field(ge=0, le=1)
    score_type: str = Field(min_length=3, max_length=100)
    source_label: str = Field(default="not provided", max_length=100)
    provenance: str = Field(min_length=3, max_length=500)
    notes: str = Field(default="", max_length=4000)

class AlertPatch(BaseModel):
    status: str = Field(pattern=r"^(new|reviewing|dismissed|escalated)$")
    notes: Optional[str] = Field(default=None, max_length=4000)
    case_id: Optional[int] = None

@router.on_event("startup")
def _startup() -> None:
    init_db()

@router.get("/summary")
def summary() -> dict[str, Any]:
    init_db()
    with connect() as con:
        cases = con.execute("SELECT status, COUNT(*) n FROM cases GROUP BY status").fetchall()
        alerts = con.execute("SELECT status, COUNT(*) n FROM alerts GROUP BY status").fetchall()
        return {"cases_total": sum(r["n"] for r in cases), "cases_by_status": {r["status"]: r["n"] for r in cases},
                "alerts_total": sum(r["n"] for r in alerts), "alerts_by_status": {r["status"]: r["n"] for r in alerts},
                "note": "Counts reflect records actually saved by analysts or score-backed alert creation; no demo records are seeded."}

@router.get("/cases")
def list_cases(status: Optional[str] = Query(default=None)) -> list[dict[str, Any]]:
    init_db()
    with connect() as con:
        if status:
            if status not in {"open", "in_review", "closed"}: raise HTTPException(400, "Invalid case status")
            rows = con.execute("SELECT * FROM cases WHERE status=? ORDER BY updated_at DESC", (status,)).fetchall()
        else:
            rows = con.execute("SELECT * FROM cases ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

@router.post("/cases", status_code=201)
def create_case(req: CaseCreate) -> dict[str, Any]:
    init_db(); stamp = now_iso()
    with connect() as con:
        cur = con.execute("INSERT INTO cases(title,dataset,entity_ref,priority,status,summary,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                           (req.title, req.dataset, req.entity_ref, req.priority, "open", req.summary, stamp, stamp))
        return dict(con.execute("SELECT * FROM cases WHERE id=?", (cur.lastrowid,)).fetchone())

@router.patch("/cases/{case_id}")
def update_case(case_id: int, req: CasePatch) -> dict[str, Any]:
    init_db(); changes = req.model_dump(exclude_none=True)
    if not changes: raise HTTPException(400, "Provide status, priority, or summary to update")
    changes["updated_at"] = now_iso()
    with connect() as con:
        if not con.execute("SELECT id FROM cases WHERE id=?", (case_id,)).fetchone(): raise HTTPException(404, "Case not found")
        con.execute("UPDATE cases SET " + ",".join(f"{k}=?" for k in changes) + " WHERE id=?", (*changes.values(), case_id))
        return dict(con.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone())

@router.get("/alerts")
def list_alerts(status: Optional[str] = Query(default=None)) -> list[dict[str, Any]]:
    init_db()
    with connect() as con:
        if status:
            if status not in {"new", "reviewing", "dismissed", "escalated"}: raise HTTPException(400, "Invalid alert status")
            rows = con.execute("SELECT * FROM alerts WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
        else:
            rows = con.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

@router.post("/alerts", status_code=201)
def create_alert(req: AlertCreate) -> dict[str, Any]:
    init_db(); stamp = now_iso()
    # Provenance is mandatory so an alert is never mistaken for a source-grounded finding.
    with connect() as con:
        cur = con.execute("INSERT INTO alerts(title,dataset,entity_ref,risk_band,score,score_type,source_label,provenance,status,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                           (req.title, req.dataset, req.entity_ref, req.risk_band, req.score, req.score_type, req.source_label, req.provenance, "new", req.notes, stamp))
        return dict(con.execute("SELECT * FROM alerts WHERE id=?", (cur.lastrowid,)).fetchone())

@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: int, req: AlertPatch) -> dict[str, Any]:
    init_db(); changes = req.model_dump(exclude_none=True)
    with connect() as con:
        if not con.execute("SELECT id FROM alerts WHERE id=?", (alert_id,)).fetchone(): raise HTTPException(404, "Alert not found")
        if changes.get("case_id") is not None and not con.execute("SELECT id FROM cases WHERE id=?", (changes["case_id"],)).fetchone():
            raise HTTPException(422, "Linked case does not exist")
        con.execute("UPDATE alerts SET " + ",".join(f"{k}=?" for k in changes) + " WHERE id=?", (*changes.values(), alert_id))
        return dict(con.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone())

@router.get("/reports/summary")
def report_summary() -> dict[str, Any]:
    init_db()
    with connect() as con:
        cases = [dict(r) for r in con.execute("SELECT status, priority, COUNT(*) count FROM cases GROUP BY status,priority")]
        alerts = [dict(r) for r in con.execute("SELECT dataset,status,risk_band,COUNT(*) count FROM alerts GROUP BY dataset,status,risk_band")]
        recent_cases = [dict(r) for r in con.execute("SELECT id,title,dataset,entity_ref,priority,status,created_at,updated_at FROM cases ORDER BY updated_at DESC LIMIT 20")]
        recent_alerts = [dict(r) for r in con.execute("SELECT id,title,dataset,entity_ref,risk_band,score,score_type,source_label,provenance,status,created_at,case_id FROM alerts ORDER BY created_at DESC LIMIT 20")]
        return {"generated_at": now_iso(), "case_breakdown": cases, "alert_breakdown": alerts, "recent_cases": recent_cases,
                "recent_alerts": recent_alerts, "data_note": "Only saved workspace records are included. This report does not imply confirmed money laundering."}

@router.get("/reports/export.csv")
def export_csv() -> StreamingResponse:
    init_db(); stream = io.StringIO(); writer = csv.writer(stream)
    writer.writerow(["record_type","id","title","dataset","entity_ref","status","priority_or_risk","score","score_type","source_label","provenance","created_at","case_id","notes"])
    with connect() as con:
        for r in con.execute("SELECT * FROM cases ORDER BY id"):
            writer.writerow(["case",r["id"],r["title"],r["dataset"],r["entity_ref"],r["status"],r["priority"],"","","","",r["created_at"],"",r["summary"]])
        for r in con.execute("SELECT * FROM alerts ORDER BY id"):
            writer.writerow(["alert",r["id"],r["title"],r["dataset"],r["entity_ref"],r["status"],r["risk_band"],r["score"],r["score_type"],r["source_label"],r["provenance"],r["created_at"],r["case_id"],r["notes"]])
    stream.seek(0)
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=amlguard_workspace_report.csv"})

@router.get("/reports/export.json")
def export_json() -> dict[str, Any]:
    return report_summary()

@router.get("/reports/evaluations")
def evaluation_files() -> dict[str, Any]:
    artifacts = ROOT / "artifacts"
    checks = {
        "elliptic": artifacts / "elliptic_evaluation.json",
        "card_fraud": artifacts / "banking_fraud_evaluation.json",
    }
    out = {}
    for key, path in checks.items():
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                out[key] = {"status": "available", "file": path.name, "metrics": payload}
            except (json.JSONDecodeError, OSError):
                out[key] = {"status": "present_but_unreadable", "file": path.name}
        else:
            out[key] = {"status": "not_generated", "file": path.name, "message": "Run the corresponding real-data training pipeline after downloading the dataset."}
    return out
