from fastapi.testclient import TestClient

from app.main import app


def test_market_snapshot_returns_mock_gold_data() -> None:
    client = TestClient(app)

    response = client.get("/api/market/snapshot")

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "XAUUSD"
    assert data["source"] == "mock"
    assert data["is_mock"] is True
    assert data["is_tradable"] is False
    assert data["bid"] < data["ask"]
    assert data["spread"] > 0
    assert data["spread"] == round(data["ask"] - data["bid"], data["digits"])
    assert data["spread_points"] == int(round(data["spread"] * (10**data["digits"])))
    assert "trading signal" in data["note"].lower()
    assert "buy" not in data["note"].lower()
    assert "sell" not in data["note"].lower()


def test_health_still_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
