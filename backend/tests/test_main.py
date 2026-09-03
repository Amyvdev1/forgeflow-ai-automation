from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_is_available(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", tmp_path / "health.db")
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_workflow_run_records_deterministic_result(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", tmp_path / "workflow.db")
    with TestClient(app) as client:
        workflows = client.get("/api/workflows").json()
        response = client.post(
            f"/api/workflows/{workflows[0]['id']}/runs",
            json={"input": "Customers cannot save an urgent support request.", "use_ai": False},
        )
        runs = client.get("/api/runs")
    assert response.status_code == 201
    body = response.json()
    assert body["execution_mode"] == "deterministic"
    assert body["result"]["priority"] == "high"
    assert runs.status_code == 200
    assert len(runs.json()) == 1


def test_ai_mode_degrades_transparently_when_not_configured(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", tmp_path / "fallback.db")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with TestClient(app) as client:
        workflow = client.get("/api/workflows").json()[0]
        response = client.post(
            f"/api/workflows/{workflow['id']}/runs",
            json={"input": "Please review this request.", "use_ai": True},
        )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "degraded"
    assert body["execution_mode"] == "deterministic_fallback"
    assert "not configured" in body["error_message"]
