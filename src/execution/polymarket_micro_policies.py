"""Micro-structure policies for high-count Polymarket workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class EdgeIntegrityResult:
    allowed: bool
    reason: str


def edge_integrity_check(*, edge: float, min_edge: float = 0.01) -> EdgeIntegrityResult:
    if edge <= 0:
        return EdgeIntegrityResult(allowed=False, reason="non_positive_edge")
    if edge < min_edge:
        return EdgeIntegrityResult(allowed=False, reason="edge_below_min")
    return EdgeIntegrityResult(allowed=True, reason="ok")


@dataclass(frozen=True)
class FanoutResult:
    allowed: bool
    reason: str


def fanout_governor(
    *,
    open_positions: int,
    per_market_legs: int,
    max_positions: int,
    max_legs: int,
) -> FanoutResult:
    if open_positions > max_positions:
        return FanoutResult(allowed=False, reason="max_positions_exceeded")
    if per_market_legs > max_legs:
        return FanoutResult(allowed=False, reason="max_legs_exceeded")
    return FanoutResult(allowed=True, reason="ok")


@dataclass(frozen=True)
class CrowdingResult:
    action: str
    reason: str


def crowding_monitor(
    *,
    fill_rate: float,
    reject_rate: float,
    edge_decay: float,
    max_reject_rate: float = 0.2,
    min_fill_rate: float = 0.6,
    max_edge_decay: float = 0.3,
) -> CrowdingResult:
    if reject_rate > max_reject_rate or fill_rate < min_fill_rate:
        return CrowdingResult(action="size_down", reason="liquidity_crowding")
    if edge_decay > max_edge_decay:
        return CrowdingResult(action="pause", reason="edge_decay")
    return CrowdingResult(action="hold", reason="ok")


@dataclass(frozen=True)
class TailRiskResult:
    allowed: bool
    reason: str


def tail_inventory_check(
    *,
    unresolved_positions: Iterable[Mapping[str, float]],
    max_total_notional: float = 500.0,
    max_age_days: float = 30.0,
) -> TailRiskResult:
    total_notional = sum(float(row.get("notional", 0.0)) for row in unresolved_positions)
    max_age = max((float(row.get("age_days", 0.0)) for row in unresolved_positions), default=0.0)
    if total_notional > max_total_notional:
        return TailRiskResult(allowed=False, reason="tail_notional_exceeded")
    if max_age > max_age_days:
        return TailRiskResult(allowed=False, reason="tail_age_exceeded")
    return TailRiskResult(allowed=True, reason="ok")


@dataclass(frozen=True)
class EfficiencyResult:
    allowed: bool
    reason: str
    efficiency: float


def micro_execution_efficiency(
    *,
    gross_pnl: float,
    fees: float,
    latency_ms: float,
    min_efficiency: float = 0.0,
) -> EfficiencyResult:
    net = gross_pnl - fees
    efficiency = net / max(1.0, latency_ms)
    if efficiency < min_efficiency:
        return EfficiencyResult(allowed=False, reason="efficiency_below_min", efficiency=float(efficiency))
    return EfficiencyResult(allowed=True, reason="ok", efficiency=float(efficiency))
