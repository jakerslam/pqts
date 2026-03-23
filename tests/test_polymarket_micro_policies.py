from __future__ import annotations

from execution.polymarket_micro_policies import (
    crowding_monitor,
    edge_integrity_check,
    fanout_governor,
    micro_execution_efficiency,
    tail_inventory_check,
)


def test_edge_integrity_and_fanout() -> None:
    assert edge_integrity_check(edge=0.02, min_edge=0.01).allowed
    assert not edge_integrity_check(edge=0.0, min_edge=0.01).allowed
    assert fanout_governor(open_positions=1, per_market_legs=1, max_positions=5, max_legs=3).allowed


def test_crowding_and_tail_risk() -> None:
    crowd = crowding_monitor(fill_rate=0.9, reject_rate=0.1, edge_decay=0.1)
    assert crowd.action == "hold"
    tail = tail_inventory_check(unresolved_positions=[{"notional": 100, "age_days": 10}], max_total_notional=200)
    assert tail.allowed


def test_micro_execution_efficiency() -> None:
    result = micro_execution_efficiency(gross_pnl=10.0, fees=1.0, latency_ms=1000, min_efficiency=0.0)
    assert result.allowed
