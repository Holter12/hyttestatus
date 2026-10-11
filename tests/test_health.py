from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_has_unavailable_values_when_vrm_not_configured(monkeypatch):
    monkeypatch.setattr("app.main.vrm_configured", lambda: False)
    response = client.get("/api/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_status"] == "unconfigured"
    assert payload["battery_soc_percent"] is None


def test_vrm_check_does_not_expose_credentials_when_unconfigured(monkeypatch):
    monkeypatch.setattr("app.main.vrm_configured", lambda: False)
    response = client.get("/api/vrm/check")
    assert response.status_code == 200
    assert response.json()["connected"] is False
    assert "token" not in response.text.lower()


def test_dashboard_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Dagens bilde" in response.text
