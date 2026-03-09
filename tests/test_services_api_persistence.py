"""Tests for SQL-backed API persistence wiring."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.config import APISettings


def _settings(database_url: str) -> APISettings:
    return APISettings(
        service_name="PQTS API Test",
        service_version="9.9.9",
        environment="test",
        database_url=database_url,
        auth_tokens="admin-token:admin,operator-token:operator,viewer-token:viewer",
    )


def _operator_headers() -> dict[str, str]:
    return {"Authorization": "Bearer operator-token"}


def _viewer_headers() -> dict[str, str]:
    return {"Authorization": "Bearer viewer-token"}


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_order_and_incident_survive_restart_with_sql_persistence(tmp_path: Path) -> None:
    db_path = tmp_path / "api-persistence.db"
    settings = _settings(_sqlite_url(db_path))
    now = datetime.now(timezone.utc).isoformat()

    order_payload = {
        "order_id": "ord-persist-1",
        "account_id": "paper-main",
        "symbol": "ETH-USD",
        "side": "buy",
        "order_type": "limit",
        "status": "open",
        "quantity": 3.0,
        "filled_quantity": 0.0,
        "remaining_quantity": 3.0,
        "submitted_at": now,
        "updated_at": now,
        "limit_price": 2_400.0,
        "time_in_force": "gtc",
    }

    incident_payload = {
        "account_id": "paper-main",
        "severity": "warning",
        "message": "spread widened",
        "code": "spread_guard",
    }

    client = TestClient(create_app(settings))
    assert client.post("/v1/execution/orders", json=order_payload, headers=_operator_headers()).status_code == 200
    assert client.post("/v1/risk/incidents", json=incident_payload, headers=_operator_headers()).status_code == 200

    restarted = TestClient(create_app(settings))
    listed = restarted.get("/v1/execution/orders", params={"account_id": "paper-main"}, headers=_viewer_headers())
    assert listed.status_code == 200
    assert any(item["order_id"] == "ord-persist-1" for item in listed.json()["orders"])

    with restarted.websocket_connect("/ws/risk?token=viewer-token&account_id=paper-main") as websocket:
        snapshot = websocket.receive_json()
        assert snapshot["event"] == "snapshot"
        incidents = snapshot["payload"]["incidents"]
        assert any(row["code"] == "spread_guard" for row in incidents)
