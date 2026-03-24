from __future__ import annotations

import asyncio

from execution.smart_router import OrderRequest, OrderType, RouteDecision, SmartOrderRouter


def test_execute_route_records_orders() -> None:
    router = SmartOrderRouter(
        {
            "enabled": True,
            "max_single_order_size": 1.0,
            "twap_interval_seconds": 0,
            "exchanges": {},
        }
    )
    order = OrderRequest(
        symbol="BTCUSDT",
        side="buy",
        quantity=1.0,
        order_type=OrderType.MARKET,
        price=100.0,
        strategy_id="test",
    )
    decision = RouteDecision(
        exchange="binance",
        order_type=OrderType.MARKET,
        price=100.0,
        split_orders=[order],
        expected_cost=0.0,
        expected_slippage=0.0,
    )
    result = asyncio.run(router.execute_route(decision))
    assert result is True
    assert router.execution_log
