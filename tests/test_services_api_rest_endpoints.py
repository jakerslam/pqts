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


def test_operator_actions_append_and_list() -> None:
    client = TestClient(create_app(_settings()))

    write = client.post(
        "/v1/operator/actions",
        json={"kind": "pause_trading", "actor": "ops", "note": "incident triage"},
        headers=_operator(),
    )
    assert write.status_code == 200
    action = write.json()["action"]
    assert action["kind"] == "pause_trading"

    listed = client.get("/v1/operator/actions", headers=_viewer())
    assert listed.status_code == 200
    actions = listed.json()["actions"]
    assert any(row["kind"] == "pause_trading" for row in actions)


def test_promotions_action_flow() -> None:
    client = TestClient(create_app(_settings()))

    baseline = client.get("/v1/promotions", headers=_viewer())
    assert baseline.status_code == 200
    records = baseline.json()["records"]
    assert any(row["strategy_id"] == "trend_following" for row in records)

    write = client.post(
        "/v1/promotions/actions",
        json={"strategy_id": "trend_following", "action": "advance", "actor": "ops"},
        headers=_operator(),
    )
    assert write.status_code == 200
    updated = write.json()["updated"]
    assert updated["strategy_id"] == "trend_following"
    assert updated["stage"] in {"shadow", "canary", "live", "paper", "backtest", "halted"}
    assert len(updated["history"]) >= 1


def test_ops_diagnostics_surfaces_return_payload_shapes() -> None:
    client = TestClient(create_app(_settings()))

    execution = client.get("/v1/ops/execution-quality", headers=_viewer())
    assert execution.status_code == 200
    assert "summary" in execution.json()
    assert "rows" in execution.json()

    truth = client.get("/v1/ops/order-truth", headers=_viewer())
    assert truth.status_code == 200
    assert "rows" in truth.json()
    assert "explanation" in truth.json()

    replay = client.get("/v1/ops/replay", headers=_viewer())
    assert replay.status_code == 200
    assert "event_types" in replay.json()
    assert "events" in replay.json()

    gallery = client.get("/v1/ops/template-gallery", headers=_viewer())
    assert gallery.status_code == 200
    assert "artifacts" in gallery.json()


def test_ops_command_endpoints_support_dry_run() -> None:
    client = TestClient(create_app(_settings()))

    presets = client.get("/v1/ops/data-seed/presets", headers=_viewer())
    assert presets.status_code == 200
    assert "presets" in presets.json()

    data_seed = client.post("/v1/ops/data-seed/run", json={"execute": False}, headers=_operator())
    assert data_seed.status_code == 200
    data_payload = data_seed.json()
    assert data_payload["dry_run"] is True
    assert "python" in data_payload["command"][0]

    notify = client.post("/v1/ops/notify/test", json={"execute": False}, headers=_operator())
    assert notify.status_code == 200
    notify_payload = notify.json()
    assert notify_payload["dry_run"] is True
    assert "python" in notify_payload["command"][0]
