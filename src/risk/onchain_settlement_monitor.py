"""On-chain settlement-state monitoring and resolution-window risk controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.persistence import EventPersistenceStore


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_ts(value: str | datetime | None, *, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value.strip():
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return fallback
    return fallback


@dataclass(frozen=True)
class SettlementMonitorConfig:
    near_resolution_window_seconds: int = 3600
    hard_resolution_window_seconds: int = 300
    near_resolution_risk_multiplier: float = 0.35
    pending_resolution_risk_multiplier: float = 0.20
    max_oracle_lag_seconds: float = 180.0
    require_confirmations: bool = True
    min_required_confirmations: int = 8


@dataclass(frozen=True)
class SettlementSnapshot:
    market_id: str
    chain_id: str
    status: str
    expected_resolution_ts: str | None
    observed_block_ts: str | None
    confirmation_count: int
    required_confirmations: int
    oracle_lag_seconds: float
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SettlementControlDecision:
    market_id: str
    action: str
    quote_enabled: bool
    allow_new_entries: bool
    max_new_risk_multiplier: float
    reason: str
    metrics: dict[str, float]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OnChainSettlementMonitor:
    """Track market settlement state and emit deterministic risk controls."""

    def __init__(
        self,
        *,
        config: SettlementMonitorConfig | None = None,
        persistence_store: EventPersistenceStore | None = None,
    ) -> None:
        self.config = config or SettlementMonitorConfig()
        self._store = persistence_store
        self._snapshots: dict[str, SettlementSnapshot] = {}

    def update_snapshot(self, snapshot: SettlementSnapshot) -> None:
        market_id = str(snapshot.market_id).strip()
        if not market_id:
            raise ValueError("market_id is required.")
        previous = self._snapshots.get(market_id)
        self._snapshots[market_id] = snapshot
        if self._store is not None:
            self._store.append(
                category="onchain_settlement_snapshots",
                payload=snapshot.to_dict(),
                timestamp=snapshot.updated_at,
            )
            if previous is None or previous.status != snapshot.status:
                self._store.append(
                    category="onchain_settlement_transitions",
                    payload={
                        "market_id": market_id,
                        "from_status": "" if previous is None else previous.status,
                        "to_status": snapshot.status,
                        "timestamp": snapshot.updated_at,
                    },
                    timestamp=snapshot.updated_at,
                )

    def _seconds_to_resolution(self, snapshot: SettlementSnapshot, *, now: datetime) -> float:
        expected = _parse_ts(snapshot.expected_resolution_ts, fallback=now)
        return float((expected - now).total_seconds())

    def _decision_for_snapshot(
        self,
        *,
        snapshot: SettlementSnapshot,
        now: datetime,
        timestamp: str,
    ) -> SettlementControlDecision:
        status = str(snapshot.status).strip().lower()
        confirmations = int(max(snapshot.confirmation_count, 0))
        required = int(
            max(
                snapshot.required_confirmations,
                self.config.min_required_confirmations,
            )
        )
        oracle_lag = max(float(snapshot.oracle_lag_seconds), 0.0)
        seconds_to_resolution = self._seconds_to_resolution(snapshot, now=now)

        action = "allow"
        quote_enabled = True
        allow_entries = True
        max_multiplier = 1.0
        reason = "Settlement state healthy."

        if status in {"disputed", "failed", "invalid"}:
            action = "halt"
            quote_enabled = False
            allow_entries = False
            max_multiplier = 0.0
            reason = f"Settlement status `{status}` is unsafe for new risk."
        elif oracle_lag > self.config.max_oracle_lag_seconds:
            action = "halt"
            quote_enabled = False
            allow_entries = False
            max_multiplier = 0.0
            reason = (
                f"Oracle lag {oracle_lag:.1f}s exceeds max {self.config.max_oracle_lag_seconds:.1f}s."
            )
        elif (
            self.config.require_confirmations
            and status in {"resolved", "finalized", "settling", "resolving"}
            and confirmations < required
        ):
            action = "halt"
            quote_enabled = False
            allow_entries = False
            max_multiplier = 0.0
            reason = f"Insufficient confirmations ({confirmations}/{required}) near settlement."
        elif seconds_to_resolution <= float(self.config.hard_resolution_window_seconds):
            action = "halt"
            quote_enabled = False
            allow_entries = False
            max_multiplier = 0.0
            reason = (
                "Entered hard resolution window; freeze new entries until settlement finality."
            )
        elif status in {"pending_resolution", "settling", "resolving"}:
            action = "reduce"
            quote_enabled = True
            allow_entries = True
            max_multiplier = float(self.config.pending_resolution_risk_multiplier)
            reason = "Pending settlement state; reduce quote size and incremental risk."
        elif seconds_to_resolution <= float(self.config.near_resolution_window_seconds):
            action = "reduce"
            quote_enabled = True
            allow_entries = True
            max_multiplier = float(self.config.near_resolution_risk_multiplier)
            reason = "Near resolution window; tighten risk before settlement."

        decision = SettlementControlDecision(
            market_id=snapshot.market_id,
            action=action,
            quote_enabled=quote_enabled,
            allow_new_entries=allow_entries,
            max_new_risk_multiplier=float(max_multiplier),
            reason=reason,
            metrics={
                "seconds_to_resolution": float(seconds_to_resolution),
                "oracle_lag_seconds": float(oracle_lag),
                "confirmation_count": float(confirmations),
                "required_confirmations": float(required),
            },
            timestamp=timestamp,
        )
        return decision

    def evaluate_market(
        self,
        *,
        market_id: str,
        now: str | datetime | None = None,
        persist: bool = True,
    ) -> SettlementControlDecision:
        key = str(market_id).strip()
        if not key:
            raise ValueError("market_id is required.")
        snapshot = self._snapshots.get(key)
        ts_now = _parse_ts(now, fallback=_utc_now())
        decision_ts = ts_now.isoformat()
        if snapshot is None:
            decision = SettlementControlDecision(
                market_id=key,
                action="halt",
                quote_enabled=False,
                allow_new_entries=False,
                max_new_risk_multiplier=0.0,
                reason="No settlement snapshot available.",
                metrics={},
                timestamp=decision_ts,
            )
        else:
            decision = self._decision_for_snapshot(snapshot=snapshot, now=ts_now, timestamp=decision_ts)

        if persist and self._store is not None:
            self._store.append(
                category="onchain_settlement_control_decisions",
                payload=decision.to_dict(),
                timestamp=decision.timestamp,
            )
        return decision

    def evaluate_all(
        self,
        *,
        now: str | datetime | None = None,
        persist: bool = True,
    ) -> list[SettlementControlDecision]:
        decisions: list[SettlementControlDecision] = []
        for market_id in sorted(self._snapshots.keys()):
            decisions.append(self.evaluate_market(market_id=market_id, now=now, persist=persist))
        return decisions

    def replay_decisions(self, *, market_id: str | None = None) -> list[SettlementControlDecision]:
        if self._store is None:
            return []
        rows = self._store.read(category="onchain_settlement_control_decisions", limit=100000)
        out: list[SettlementControlDecision] = []
        for row in reversed(rows):
            payload = dict(row.payload)
            if market_id is not None and str(payload.get("market_id")) != str(market_id):
                continue
            out.append(SettlementControlDecision(**payload))
        return out
