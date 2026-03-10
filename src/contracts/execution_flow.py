"""Typed contracts for execution-flow boundaries.

These models keep strategy/risk/router payloads explicit and stable across
CLI, API, and web surfaces.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class OrderIntent:
    """Canonical order intent at router ingress."""

    order_id: str
    strategy_id: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    requested_price: float
    expected_alpha_bps: float
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["created_at"] = self.created_at.isoformat()
        return out


@dataclass(frozen=True)
class RoutePreview:
    """Pre-execution router preview contract."""

    venue: str
    ranked_venues: list[str]
    order_type: str
    expected_cost_usd: float
    expected_slippage_usd: float
    predicted_total_router_bps: float
    predicted_net_alpha_bps: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionOutcome:
    """Post-execution summary contract for audit surfaces."""

    success: bool
    decision: str
    order_id: str | None
    venue: str | None
    rejected_reason: str | None
    latency_ms: float | None = None
    fill_ratio: float | None = None
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["created_at"] = self.created_at.isoformat()
        return out

