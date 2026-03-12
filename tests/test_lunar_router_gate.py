from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from execution.risk_aware_router import RiskAwareRouter
from execution.smart_router import OrderRequest, OrderType
from risk.kill_switches import RiskLimits


def _market_data(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    return {
        "binance": {
            symbol: {
                "price": 50000.0,
                "spread": 0.0002,
                "volume_24h": 2_000_000.0,
            }
        },
        "order_book": {
            "bids": [(49990.0, 2.0), (49980.0, 3.0)],
            "asks": [(50010.0, 2.0), (50020.0, 3.0)],
        },
    }


def _portfolio() -> Dict[str, Any]:
    return {
        "positions": {},
        "prices": {"BTCUSDT": 50000.0},
        "total_pnl": 0.0,
        "unrealized_pnl": 0.0,
        "realized_pnl": 0.0,
        "gross_exposure": 0.0,
        "net_exposure": 0.0,
        "leverage": 0.0,
        "open_orders": [],
    }


def _router(tmp_path: Path) -> RiskAwareRouter:
    router = RiskAwareRouter(
        risk_config=RiskLimits(
            max_daily_loss_pct=0.02,
            max_drawdown_pct=0.15,
            max_gross_leverage=2.0,
        ),
        broker_config={
            "enabled": True,
            "live_execution": False,
            "tca_db_path": str(tmp_path / "tca.csv"),
            "order_ledger_path": str(tmp_path / "order_ledger.jsonl"),
            "lunar_edge_gate": {
                "enabled": True,
                "min_net_edge_bps": 10.0,
                "require_timestamps": True,
            },
        },
    )
    router.set_capital(100000.0, source="unit_test")
    return router


def test_router_lunar_gate_blocks_when_context_missing(tmp_path) -> None:
    router = _router(tmp_path)
    order = OrderRequest(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.01,
        order_type=OrderType.LIMIT,
        price=50000.0,
        expected_alpha_bps=100.0,
    )
    result = asyncio.run(
        router.submit_order(
            order=order,
            market_data=_market_data(order.symbol),
            portfolio=_portfolio(),
            strategy_returns={"baseline": [0.0] * 30},
            portfolio_changes=[0.0] * 30,
        )
    )
    assert result.success is False
    assert "LUNAR_NET_EDGE_GATE" in str(result.rejected_reason)
    gate = result.audit_log.get("lunar_net_edge_gate", {})
    assert gate.get("passed") is False


def test_router_lunar_gate_allows_when_context_passes(tmp_path) -> None:
    router = _router(tmp_path)
    order = OrderRequest(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.01,
        order_type=OrderType.LIMIT,
        price=50000.0,
        expected_alpha_bps=100.0,
        decision_context={
            "model_probability": 0.57,
            "market_probability": 0.51,
            "fee_bps": 2.0,
            "spread_bps": 1.5,
            "slippage_bps": 1.0,
            "latency_penalty_bps": 0.5,
            "min_net_edge_bps": 10.0,
            "evidence_ts_ms": 1_000,
            "market_ts_ms": 1_400,
            "now_ts_ms": 2_000,
        },
    )
    result = asyncio.run(
        router.submit_order(
            order=order,
            market_data=_market_data(order.symbol),
            portfolio=_portfolio(),
            strategy_returns={"baseline": [0.0] * 30},
            portfolio_changes=[0.0] * 30,
        )
    )
    assert result.success is True
    gate = result.audit_log.get("lunar_net_edge_gate", {})
    assert gate.get("passed") is True
