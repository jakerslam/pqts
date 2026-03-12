from __future__ import annotations

import asyncio
from dataclasses import dataclass

from execution.copy_trade_guardrails import (
    CopyTradePolicy,
    CopyTradeSafetyEnvelope,
    CopyTradeSignal,
)


@dataclass
class _RouterResult:
    success: bool


class _FakeRouter:
    def __init__(self) -> None:
        self.calls = []

    async def submit_order(self, order, market_data, portfolio, **kwargs):  # noqa: ANN001
        self.calls.append({"order": order, "market_data": market_data, "portfolio": portfolio, "kwargs": kwargs})
        return _RouterResult(success=True)


def test_copy_trade_envelope_blocks_non_allowlisted_or_budget_breaches() -> None:
    envelope = CopyTradeSafetyEnvelope(
        CopyTradePolicy(
            allowed_leaders=("leader_a",),
            max_signal_notional_usd=500.0,
            max_total_follow_notional_usd=1_000.0,
            drawdown_kill_switch_pct=0.10,
        )
    )
    decision = envelope.evaluate(
        signal=CopyTradeSignal(
            leader_id="leader_b",
            symbol="BTCUSDT",
            side="buy",
            quantity=2.0,
            price=400.0,
        ),
        current_drawdown_pct=0.12,
        kill_switch_active=False,
    )
    assert decision.accepted is False
    assert "leader_not_allowlisted" in decision.reason_codes
    assert "signal_notional_limit_exceeded" in decision.reason_codes
    assert "drawdown_kill_switch_triggered" in decision.reason_codes


def test_copy_trade_envelope_submits_only_through_router_path() -> None:
    envelope = CopyTradeSafetyEnvelope(
        CopyTradePolicy(
            allowed_leaders=("leader_a",),
            max_signal_notional_usd=5_000.0,
            max_total_follow_notional_usd=10_000.0,
            drawdown_kill_switch_pct=0.20,
        )
    )
    router = _FakeRouter()
    signal = CopyTradeSignal(
        leader_id="leader_a",
        symbol="ETHUSDT",
        side="buy",
        quantity=1.0,
        price=200.0,
        expected_alpha_bps=12.0,
    )
    decision, result = asyncio.run(
        envelope.submit_follow_signal(
            router=router,
            signal=signal,
            market_data={"binance": {"ETHUSDT": {"price": 200.0}}},
            portfolio={"positions": {}},
            current_drawdown_pct=0.02,
            kill_switch_active=False,
        )
    )
    assert decision.accepted is True
    assert result is not None
    assert len(router.calls) == 1
    submitted = router.calls[0]["order"]
    assert submitted.strategy_id == "copytrade_follow"
    assert submitted.decision_context["copytrade_leader_id"] == "leader_a"
