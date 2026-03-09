"""Tests for on-chain settlement-state monitoring and risk controls."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.persistence import EventPersistenceStore
from risk.onchain_settlement_monitor import OnChainSettlementMonitor, SettlementSnapshot


def _iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat()


def test_near_resolution_triggers_reduce() -> None:
    now = datetime(2026, 3, 9, 22, 0, 0, tzinfo=timezone.utc)
    monitor = OnChainSettlementMonitor()
    monitor.update_snapshot(
        SettlementSnapshot(
            market_id="MKT-1",
            chain_id="137",
            status="open",
            expected_resolution_ts=_iso(now + timedelta(minutes=20)),
            observed_block_ts=_iso(now),
            confirmation_count=20,
            required_confirmations=8,
            oracle_lag_seconds=20.0,
        )
    )
    decision = monitor.evaluate_market(market_id="MKT-1", now=now)
    assert decision.action == "reduce"
    assert 0.0 < decision.max_new_risk_multiplier < 1.0


def test_disputed_market_halts_quotes() -> None:
    now = datetime(2026, 3, 9, 22, 0, 0, tzinfo=timezone.utc)
    monitor = OnChainSettlementMonitor()
    monitor.update_snapshot(
        SettlementSnapshot(
            market_id="MKT-2",
            chain_id="1",
            status="disputed",
            expected_resolution_ts=_iso(now + timedelta(hours=2)),
            observed_block_ts=_iso(now),
            confirmation_count=50,
            required_confirmations=8,
            oracle_lag_seconds=10.0,
        )
    )
    decision = monitor.evaluate_market(market_id="MKT-2", now=now)
    assert decision.action == "halt"
    assert decision.quote_enabled is False
    assert decision.allow_new_entries is False


def test_insufficient_confirmations_halts_near_settlement() -> None:
    now = datetime(2026, 3, 9, 22, 0, 0, tzinfo=timezone.utc)
    monitor = OnChainSettlementMonitor()
    monitor.update_snapshot(
        SettlementSnapshot(
            market_id="MKT-3",
            chain_id="1",
            status="resolved",
            expected_resolution_ts=_iso(now + timedelta(minutes=45)),
            observed_block_ts=_iso(now),
            confirmation_count=2,
            required_confirmations=12,
            oracle_lag_seconds=15.0,
        )
    )
    decision = monitor.evaluate_market(market_id="MKT-3", now=now)
    assert decision.action == "halt"
    assert "Insufficient confirmations" in decision.reason


def test_persistence_replay(tmp_path: Path) -> None:
    now = datetime(2026, 3, 9, 22, 0, 0, tzinfo=timezone.utc)
    store = EventPersistenceStore(dsn=f"sqlite:///{tmp_path}/settlement.db")
    monitor = OnChainSettlementMonitor(persistence_store=store)
    monitor.update_snapshot(
        SettlementSnapshot(
            market_id="MKT-4",
            chain_id="8453",
            status="open",
            expected_resolution_ts=_iso(now + timedelta(days=1)),
            observed_block_ts=_iso(now),
            confirmation_count=25,
            required_confirmations=8,
            oracle_lag_seconds=5.0,
        )
    )
    decision = monitor.evaluate_market(market_id="MKT-4", now=now)
    assert decision.action == "allow"

    replayed = monitor.replay_decisions(market_id="MKT-4")
    assert len(replayed) == 1
    assert replayed[0].action == "allow"
