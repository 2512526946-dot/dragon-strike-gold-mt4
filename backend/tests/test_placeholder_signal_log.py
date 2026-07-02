import json

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


FORBIDDEN_ACTION_VALUES = {
    "buy",
    "sell",
    "long",
    "short",
    "open_position",
    "close_position",
}


def test_placeholder_signal_log_writes_jsonl(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIGNAL_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("PLACEHOLDER_SIGNAL_LOG_FILE", "placeholder_signals.jsonl")
    get_settings.cache_clear()
    client = TestClient(app)

    response = client.post("/api/signals/placeholder/log")

    assert response.status_code == 200
    data = response.json()
    assert data["logged"] is True
    assert data["log_id"].startswith("log-")
    assert data["log_type"] == "placeholder_signal"
    assert data["source"] == "placeholder"
    assert data["symbol"] == "XAUUSD"
    assert data["signal_id"].startswith("placeholder-")
    assert data["action"] in {"observe_only", "no_trade"}
    assert data["signal_type"] == "placeholder_only"
    assert data["lifecycle_status"] == "CREATED"
    assert data["is_placeholder"] is True
    assert data["is_tradable"] is False
    assert data["final_score"] == 0
    assert data["suggested_lot"] == 0
    assert data["allow_chasing"] is False
    assert "not a trading recommendation" in data["note"].lower()

    log_path = tmp_path / "placeholder_signals.jsonl"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    log_entry = json.loads(lines[0])
    assert log_entry["log_id"] == data["log_id"]
    assert log_entry["log_type"] == "placeholder_signal"
    assert log_entry["is_placeholder"] is True
    assert log_entry["is_tradable"] is False
    assert log_entry["final_score"] == 0
    assert log_entry["suggested_lot"] == 0
    assert log_entry["allow_chasing"] is False

    payload = json.dumps(data).lower() + lines[0].lower()
    for forbidden_value in FORBIDDEN_ACTION_VALUES:
        assert forbidden_value not in payload

    get_settings.cache_clear()


def test_existing_endpoints_still_pass() -> None:
    get_settings.cache_clear()
    client = TestClient(app)

    health_response = client.get("/health")
    market_response = client.get("/api/market/snapshot")
    placeholder_response = client.get("/api/signals/placeholder")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert market_response.status_code == 200
    assert market_response.json()["source"] == "mock"
    assert placeholder_response.status_code == 200
    assert placeholder_response.json()["source"] == "placeholder"
