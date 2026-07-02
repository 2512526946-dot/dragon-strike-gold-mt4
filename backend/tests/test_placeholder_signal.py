import json

from fastapi.testclient import TestClient

from app.main import app


FORBIDDEN_ACTION_VALUES = {
    "buy",
    "sell",
    "long",
    "short",
    "open_position",
    "close_position",
}


def test_placeholder_signal_returns_non_tradable_placeholder() -> None:
    client = TestClient(app)

    response = client.get("/api/signals/placeholder")

    assert response.status_code == 200
    data = response.json()
    assert data["signal_id"].startswith("placeholder-")
    assert data["symbol"] == "XAUUSD"
    assert data["source"] == "placeholder"
    assert data["action"] in {"observe_only", "no_trade"}
    assert data["signal_type"] == "placeholder_only"
    assert data["lifecycle_status"] == "CREATED"
    assert data["market_regime"] == "unknown"
    assert data["final_score"] == 0
    assert data["entry_zone"] == {"low": None, "high": None}
    assert data["confirm_condition"] == "No real confirmation condition. Placeholder only."
    assert data["stop_loss"] is None
    assert data["take_profit_1"] is None
    assert data["take_profit_2"] is None
    assert data["invalidation_condition"] == "N/A"
    assert data["allow_chasing"] is False
    assert data["risk_level"] == "none"
    assert data["leverage_10x_status"] == "not_evaluated"
    assert data["suggested_lot"] == 0
    assert data["is_placeholder"] is True
    assert data["is_tradable"] is False
    assert "not a trading recommendation" in data["note"].lower()


def test_placeholder_signal_response_has_no_real_action_values() -> None:
    client = TestClient(app)

    response = client.get("/api/signals/placeholder")

    assert response.status_code == 200
    payload = json.dumps(response.json()).lower()
    for forbidden_value in FORBIDDEN_ACTION_VALUES:
        assert forbidden_value not in payload


def test_existing_health_and_market_snapshot_still_pass() -> None:
    client = TestClient(app)

    health_response = client.get("/health")
    market_response = client.get("/api/market/snapshot")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert market_response.status_code == 200
    assert market_response.json()["source"] == "mock"
