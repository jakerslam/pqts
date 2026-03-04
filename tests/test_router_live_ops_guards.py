"""Deterministic tests for router idempotency and live rate-limit guards."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.risk_aware_router import RiskAwareRouter, VenueClient
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


def _router(tmp_path: Path, **broker_overrides: Any) -> RiskAwareRouter:
    broker_config = {
        "enabled": True,
        "live_execution": False,
        "tca_db_path": str(tmp_path / "tca.csv"),
        "order_ledger_path": str(tmp_path / "order_ledger.jsonl"),
    }
    broker_config.update(broker_overrides)
    router = RiskAwareRouter(
        risk_config=RiskLimits(
            max_daily_loss_pct=0.02,
            max_drawdown_pct=0.15,
            max_gross_leverage=2.0,
        ),
        broker_config=broker_config,
    )
    router.set_capital(100000.0, source="unit_test")
    return router


async def _submit(router: RiskAwareRouter, order: OrderRequest):
    return await router.submit_order(
        order=order,
        market_data=_market_data(order.symbol),
        portfolio=_portfolio(),
        strategy_returns={"baseline": [0.0] * 30},
        portfolio_changes=[0.0] * 30,
    )


def test_router_blocks_duplicate_client_order_intent(tmp_path):
    router = _router(tmp_path)
    order_1 = OrderRequest(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.01,
        order_type=OrderType.LIMIT,
        price=50000.0,
        client_order_id="dup-1",
    )
    order_2 = OrderRequest(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.01,
        order_type=OrderType.LIMIT,
        price=50000.0,
        client_order_id="dup-1",
    )

    first = asyncio.run(_submit(router, order_1))
    second = asyncio.run(_submit(router, order_2))

    assert first.success is True
    assert second.success is False
    assert "IDEMPOTENCY_DUPLICATE" in str(second.rejected_reason)
    stats = router.get_stats()
    assert stats["live_ops_controls"]["idempotency_rejects"] == 1


def test_live_router_requires_client_order_id_when_enabled(tmp_path):
    router = _router(tmp_path, live_execution=True, require_live_client_order_id=True)
    order = OrderRequest(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.01,
        order_type=OrderType.LIMIT,
        price=50000.0,
    )

    result = asyncio.run(_submit(router, order))

    assert result.success is False
    assert result.rejected_reason == "LIVE_REQUIRES_CLIENT_ORDER_ID"


class _DummyLiveAdapter:
    async def place_order(self, **_kwargs: Any) -> Dict[str, Any]:
        return {"status": "accepted"}


def test_live_router_blocks_rate_limited_venue_orders(tmp_path):
    router = _router(
        tmp_path,
        live_execution=True,
        require_live_client_order_id=True,
        rate_limits={
            "binance": {
                "order_create": {"limit": 1, "window_seconds": 60.0},
            }
        },
    )
    router.market_venues["binance"] = VenueClient(
        market="crypto",
        venue="binance",
        symbols=["BTCUSDT"],
        adapter=_DummyLiveAdapter(),
        connected=True,
        is_stub=False,
    )

    first = OrderRequest(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.01,
        order_type=OrderType.LIMIT,
        price=50000.0,
        client_order_id="rl-1",
    )
    second = OrderRequest(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.01,
        order_type=OrderType.LIMIT,
        price=50000.0,
        client_order_id="rl-2",
    )

    result_1 = asyncio.run(_submit(router, first))
    result_2 = asyncio.run(_submit(router, second))

    assert result_1.success is True
    assert result_2.success is False
    assert "RATE_LIMIT_EXCEEDED" in str(result_2.rejected_reason)
    stats = router.get_stats()
    assert stats["live_ops_controls"]["rate_limit_rejects"] == 1
