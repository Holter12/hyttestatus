from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_marks_vrm_unconfigured():
    response = client.get("/api/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_status"] == "demo"
    assert payload["battery_soc_percent"] is None


def test_dashboard_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Dagens bilde" in response.text
