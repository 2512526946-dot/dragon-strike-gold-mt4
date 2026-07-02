from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_project_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "project": "巨龙出击",
        "name": "dragon-strike-gold-mt4",
        "status": "ok",
        "version": "0.1.0",
        "stage": "development_skeleton",
    }
