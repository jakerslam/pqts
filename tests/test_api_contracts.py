"""Tests for canonical API/domain contracts."""

from __future__ import annotations

from datetime import datetime, timezone

from contracts import (
    AccountSummary,
    ErrorCategory,
    ErrorEnvelope,
    OrderSide,
    OrderSnapshot,
    OrderStatus,
    OrderType,
    PnLSnapshot,
    PositionDirection,
    PositionSnapshot,
    RiskLevel,
    RiskStateSnapshot,
    TimeInForce,
    ToolPayload,
    ToolStatus,
    batch_to_dict,
)


def test_account_summary_round_trip_dict() -> None:
    summary = AccountSummary(
        account_id="acct-1",
        cash=1000.0,
        equity=1200.0,
        buying_power=2500.0,
        realized_pnl=75.0,
        unrealized_pnl=125.0,
    )
    payload = summary.to_dict()
    assert payload["account_id"] == "acct-1"
    assert isinstance(payload["as_of"], str)

    round_trip = AccountSummary.from_dict(payload)
    assert round_trip.account_id == summary.account_id
    assert round_trip.buying_power == summary.buying_power


def test_position_order_fill_pnl_risk_contracts_serialize_enums() -> None:
    created = datetime(2026, 3, 9, tzinfo=timezone.utc)

    position = PositionSnapshot(
        position_id="pos-1",
        account_id="acct-1",
        symbol="AAPL",
        direction=PositionDirection.LONG,
        quantity=5,
        avg_price=180,
        mark_price=185,
        market_value=925,
        unrealized_pnl=25,
        as_of=created,
    )
    order = OrderSnapshot(
        order_id="ord-1",
        account_id="acct-1",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        status=OrderStatus.OPEN,
        quantity=10,
        filled_quantity=5,
        remaining_quantity=5,
        limit_price=184.5,
        submitted_at=created,
        updated_at=created,
        time_in_force=TimeInForce.DAY,
    )
    pnl = PnLSnapshot(
        account_id="acct-1",
        period_start=created,
        period_end=created,
        realized_pnl=25,
        unrealized_pnl=50,
        gross_pnl=75,
        net_pnl=72,
        fees=3,
    )
    risk = RiskStateSnapshot(
        account_id="acct-1",
        risk_level=RiskLevel.ELEVATED,
        max_drawdown=0.2,
        current_drawdown=0.12,
        var_95=2500,
        exposure=11000,
        kill_switch_active=False,
        reasons=["drawdown rising"],
        as_of=created,
    )

    payload = batch_to_dict([position, order, pnl, risk])
    assert payload[0]["direction"] == "long"
    assert payload[1]["side"] == "buy"
    assert payload[1]["order_type"] == "limit"
    assert payload[1]["time_in_force"] == "day"
    assert payload[3]["risk_level"] == "elevated"


def test_tool_payload_and_error_envelope_round_trip() -> None:
    err = ErrorEnvelope(
        code="provider_timeout",
        message="Provider call timed out",
        category=ErrorCategory.PROVIDER,
        retryable=True,
        trace_id="trace-123",
    )
    payload = ToolPayload(
        tool_name="search-web",
        invocation_id="tool-1",
        status=ToolStatus.FAILED,
        args={"query": "latest btc news"},
        error=err,
    )

    serialized = payload.to_dict()
    assert serialized["status"] == "failed"
    assert serialized["error"]["category"] == "provider"
    assert serialized["error"]["trace_id"] == "trace-123"

    restored = ToolPayload.from_dict(serialized)
    assert restored.status == ToolStatus.FAILED
    assert restored.error is not None
    assert restored.error.category == ErrorCategory.PROVIDER
    assert restored.error.retryable is True

