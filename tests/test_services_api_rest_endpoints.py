"""Tests for core API REST resources."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.config import APISettings


def _settings() -> APISettings:
    return APISettings(
        service_name="PQTS API Test",
        service_version="9.9.9",
        environment="test",
        auth_tokens="admin-token:admin,operator-token:operator,viewer-token:viewer",
    )


def _viewer() -> dict[str, str]:
    return {"Authorization": "Bearer viewer-token"}


def _operator() -> dict[str, str]:
    return {"Authorization": "Bearer operator-token"}


def test_get_account_summary_for_default_bootstrap_account() -> None:
    client = TestClient(create_app(_settings()))
    response = client.get("/v1/accounts/paper-main", headers=_viewer())
    assert response.status_code == 200
    payload = response.json()["account"]
    assert payload["account_id"] == "paper-main"
    assert payload["currency"] == "USD"


def test_post_order_requires_operator_role() -> None:
    client = TestClient(create_app(_settings()))
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "order_id": "ord-1",
        "account_id": "paper-main",
        "symbol": "BTC-USD",
        "side": "buy",
        "order_type": "limit",
        "status": "open",
        "quantity": 1.0,
        "filled_quantity": 0.0,
        "remaining_quantity": 1.0,
        "submitted_at": now,
        "updated_at": now,
        "limit_price": 40_000.0,
        "stop_price": None,
        "time_in_force": "gtc",
    }

    denied = client.post("/v1/execution/orders", json=payload, headers=_viewer())
    assert denied.status_code == 403

    allowed = client.post("/v1/execution/orders", json=payload, headers=_operator())
    assert allowed.status_code == 200

    listed = client.get("/v1/execution/orders", params={"account_id": "paper-main"}, headers=_viewer())
    assert listed.status_code == 200
    orders = listed.json()["orders"]
    assert any(item["order_id"] == "ord-1" for item in orders)


def test_risk_state_upsert_and_fetch() -> None:
    client = TestClient(create_app(_settings()))
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "risk_level": "elevated",
        "max_drawdown": 0.15,
        "current_drawdown": 0.07,
        "var_95": 0.03,
        "exposure": 0.42,
        "kill_switch_active": False,
        "reasons": ["volatility_spike"],
        "as_of": now,
    }

    write = client.put("/v1/risk/state/paper-main", json=payload, headers=_operator())
    assert write.status_code == 200
    assert write.json()["risk_state"]["risk_level"] == "elevated"

    read = client.get("/v1/risk/state/paper-main", headers=_viewer())
    assert read.status_code == 200
    assert read.json()["risk_state"]["current_drawdown"] == 0.07
