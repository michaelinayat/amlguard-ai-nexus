from fastapi.testclient import TestClient
from app.main import app
import app.workspace as workspace


def test_cases_alerts_and_reports_are_persisted_without_seed_data(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "DB_PATH", tmp_path / "workspace.db")
    with TestClient(app) as client:
        assert client.get("/workspace/cases").json() == []
        assert client.get("/workspace/alerts").json() == []

        case_response = client.post("/workspace/cases", json={
            "title": "Test transaction review", "dataset": "elliptic",
            "entity_ref": "test-tx-1", "priority": "high", "summary": "Test record only."
        })
        assert case_response.status_code == 201
        case = case_response.json()
        assert case["status"] == "open"

        alert_response = client.post("/workspace/alerts", json={
            "title": "Test model score alert", "dataset": "elliptic", "entity_ref": "test-tx-1",
            "risk_band": "HIGH", "score": 0.81, "score_type": "test_probability",
            "source_label": "not provided", "provenance": "automated test fixture",
            "notes": "Test fixture; not a real finding."
        })
        assert alert_response.status_code == 201
        alert = alert_response.json()
        assert alert["provenance"] == "automated test fixture"

        assert client.patch(f"/workspace/cases/{case['id']}", json={"status": "in_review"}).json()["status"] == "in_review"
        assert client.patch(f"/workspace/alerts/{alert['id']}", json={"status": "reviewing"}).json()["status"] == "reviewing"
        report = client.get("/workspace/reports/summary").json()
        assert len(report["recent_cases"]) == 1
        assert len(report["recent_alerts"]) == 1
        csv_response = client.get("/workspace/reports/export.csv")
        assert csv_response.status_code == 200
        assert "Test model score alert" in csv_response.text


def test_alert_requires_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "DB_PATH", tmp_path / "workspace.db")
    with TestClient(app) as client:
        response = client.post("/workspace/alerts", json={
            "title": "Missing provenance", "dataset": "elliptic", "entity_ref": "tx1",
            "risk_band": "HIGH", "score": 0.9, "score_type": "probability"
        })
        assert response.status_code == 422
