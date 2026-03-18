"""Bankroll-aware utility policy compilation and fee-dominance gating."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_UTILITY_MODES = {"preserve", "balanced", "speculative"}


@dataclass(frozen=True)
class CapitalUtilityInputs:
    """User-declared capital utility contract inputs."""

    bankroll: float
    utility_mode: str
    time_horizon_days: int
    max_loss_budget_pct: float
    speculative_acknowledged: bool = False

    def __post_init__(self) -> None:
        if float(self.bankroll) <= 0.0:
            raise ValueError("bankroll must be > 0")
        mode = str(self.utility_mode).strip().lower()
        if mode not in _UTILITY_MODES:
            raise ValueError(f"unsupported utility_mode: {self.utility_mode}")
        if int(self.time_horizon_days) <= 0:
            raise ValueError("time_horizon_days must be > 0")
        budget = float(self.max_loss_budget_pct)
        if budget <= 0.0 or budget > 1.0:
            raise ValueError("max_loss_budget_pct must be in (0, 1]")


@dataclass(frozen=True)
class StrategyCostModel:
    """Per-strategy economic feasibility model."""

    strategy_class: str
    venue: str
    min_efficient_capital: float
    min_ticket_notional: float
    expected_edge_bps: float
    fee_bps: float
    slippage_bps: float
    diversification_slots: int = 2

    def __post_init__(self) -> None:
        if not str(self.strategy_class).strip():
            raise ValueError("strategy_class is required")
        if not str(self.venue).strip():
            raise ValueError("venue is required")
        if float(self.min_efficient_capital) <= 0.0:
            raise ValueError("min_efficient_capital must be > 0")
        if float(self.min_ticket_notional) <= 0.0:
            raise ValueError("min_ticket_notional must be > 0")
        if int(self.diversification_slots) <= 0:
            raise ValueError("diversification_slots must be > 0")


@dataclass(frozen=True)
class EfficientCapitalDecision:
    """Result of minimum-efficient-capital gating for one strategy class."""

    strategy_class: str
    venue: str
    status: str
    min_required_capital: float
    downgrade_target: str | None
    drivers: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "strategy_class": self.strategy_class,
            "venue": self.venue,
            "status": self.status,
            "min_required_capital": float(self.min_required_capital),
            "downgrade_target": self.downgrade_target,
            "drivers": list(self.drivers),
        }


@dataclass(frozen=True)
class FeeDominanceDecision:
    """Per-order after-cost edge decision for micro/small accounts."""

    action: str
    expected_after_cost_edge_bps: float
    burden_ratio: float
    reasons: tuple[str, ...]
    recommendations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "expected_after_cost_edge_bps": float(self.expected_after_cost_edge_bps),
            "burden_ratio": float(self.burden_ratio),
            "reasons": list(self.reasons),
            "recommendations": list(self.recommendations),
        }


@dataclass(frozen=True)
class CompiledCapitalPolicy:
    """Compiled bankroll-aware policy used before capital-affecting workflows."""

    utility_mode: str
    strategy_allowlist: tuple[str, ...]
    position_size_bounds: dict[str, float]
    concurrent_position_limit: int
    cadence_budget_per_day: int
    drawdown_loss_envelope: dict[str, float]
    acknowledgements: tuple[str, ...]
    strategy_decisions: tuple[EfficientCapitalDecision, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "utility_mode": self.utility_mode,
            "strategy_allowlist": list(self.strategy_allowlist),
            "position_size_bounds": dict(self.position_size_bounds),
            "concurrent_position_limit": int(self.concurrent_position_limit),
            "cadence_budget_per_day": int(self.cadence_budget_per_day),
            "drawdown_loss_envelope": dict(self.drawdown_loss_envelope),
            "acknowledgements": list(self.acknowledgements),
            "strategy_decisions": [row.as_dict() for row in self.strategy_decisions],
        }


def _utility_limits(mode: str) -> dict[str, float]:
    token = str(mode).strip().lower()
    limits = {
        "preserve": {
            "max_position_pct": 0.02,
            "drawdown_pct": 0.10,
            "cadence_budget_per_day": 4.0,
            "concurrent_positions": 3.0,
        },
        "balanced": {
            "max_position_pct": 0.05,
            "drawdown_pct": 0.20,
            "cadence_budget_per_day": 12.0,
            "concurrent_positions": 6.0,
        },
        "speculative": {
            "max_position_pct": 0.10,
            "drawdown_pct": 0.75,
            "cadence_budget_per_day": 10.0,
            "concurrent_positions": 4.0,
        },
    }
    if token not in limits:
        raise ValueError(f"unsupported utility mode: {mode}")
    return limits[token]


def evaluate_min_efficient_capital(
    *,
    inputs: CapitalUtilityInputs,
    model: StrategyCostModel,
    downgrade_target: str | None = "research_only",
) -> EfficientCapitalDecision:
    """Gate strategy classes when bankroll is below economic viability thresholds."""

    required_capital = max(
        float(model.min_efficient_capital),
        float(model.min_ticket_notional) * float(model.diversification_slots),
    )
    if float(inputs.bankroll) >= required_capital:
        return EfficientCapitalDecision(
            strategy_class=model.strategy_class,
            venue=model.venue,
            status="eligible",
            min_required_capital=required_capital,
            downgrade_target=None,
            drivers=(),
        )

    if (
        str(inputs.utility_mode).strip().lower() == "speculative"
        and bool(inputs.speculative_acknowledged)
        and float(inputs.max_loss_budget_pct) >= 0.30
        and float(inputs.bankroll) >= float(model.min_ticket_notional)
    ):
        return EfficientCapitalDecision(
            strategy_class=model.strategy_class,
            venue=model.venue,
            status="speculative_only",
            min_required_capital=required_capital,
            downgrade_target=str(downgrade_target).strip() or "speculative_only",
            drivers=("insufficient_efficient_capital", "speculative_mode_override"),
        )

    return EfficientCapitalDecision(
        strategy_class=model.strategy_class,
        venue=model.venue,
        status="blocked",
        min_required_capital=required_capital,
        downgrade_target=str(downgrade_target).strip() or "research_only",
        drivers=("insufficient_efficient_capital",),
    )


def evaluate_fee_dominance(
    *,
    ticket_notional: float,
    expected_edge_bps: float,
    fee_bps: float,
    slippage_bps: float,
    min_efficient_ticket_notional: float,
    burden_cap_ratio: float = 0.65,
) -> FeeDominanceDecision:
    """Compute after-cost edge and return deterministic policy action."""

    ticket = float(ticket_notional)
    if ticket <= 0.0:
        raise ValueError("ticket_notional must be > 0")
    expected = float(expected_edge_bps)
    burden = max(float(fee_bps), 0.0) + max(float(slippage_bps), 0.0)
    after_cost_edge = expected - burden
    denominator = max(abs(expected), 1e-9)
    burden_ratio = burden / denominator

    reasons: list[str] = []
    recommendations: list[str] = []
    if after_cost_edge <= 0.0:
        reasons.append("after_cost_edge_non_positive")
        recommendations.extend(
            [
                "increase_ticket_size_to_efficient_threshold",
                "switch_to_lower_fee_or_lower_cadence_strategy",
                "no_trade",
            ]
        )
        return FeeDominanceDecision(
            action="block",
            expected_after_cost_edge_bps=after_cost_edge,
            burden_ratio=burden_ratio,
            reasons=tuple(reasons),
            recommendations=tuple(recommendations),
        )
    if burden_ratio >= float(burden_cap_ratio):
        reasons.append("fee_slippage_burden_elevated")
        recommendations.extend(
            [
                "reduce_cadence",
                "prefer_larger_efficient_tickets",
            ]
        )
        return FeeDominanceDecision(
            action="cadence_cap",
            expected_after_cost_edge_bps=after_cost_edge,
            burden_ratio=burden_ratio,
            reasons=tuple(reasons),
            recommendations=tuple(recommendations),
        )
    if ticket < float(min_efficient_ticket_notional):
        reasons.append("ticket_below_efficient_floor")
        recommendations.append("size_adjust_up_or_no_trade")
        return FeeDominanceDecision(
            action="size_adjust",
            expected_after_cost_edge_bps=after_cost_edge,
            burden_ratio=burden_ratio,
            reasons=tuple(reasons),
            recommendations=tuple(recommendations),
        )
    return FeeDominanceDecision(
        action="allow",
        expected_after_cost_edge_bps=after_cost_edge,
        burden_ratio=burden_ratio,
        reasons=(),
        recommendations=(),
    )


def compile_bankroll_aware_policy(
    *,
    inputs: CapitalUtilityInputs,
    strategy_models: list[StrategyCostModel],
    downgrade_targets: dict[str, str] | None = None,
) -> CompiledCapitalPolicy:
    """Compile an effective strategy/risk envelope from bankroll and declared utility."""

    mode = str(inputs.utility_mode).strip().lower()
    if mode == "speculative" and not bool(inputs.speculative_acknowledged):
        raise RuntimeError("speculative mode requires explicit max-loss acknowledgement")

    limits = _utility_limits(mode)
    decisions: list[EfficientCapitalDecision] = []
    allowlist: list[str] = []
    downgrade_map = downgrade_targets or {}
    for model in strategy_models:
        decision = evaluate_min_efficient_capital(
            inputs=inputs,
            model=model,
            downgrade_target=downgrade_map.get(model.strategy_class, "research_only"),
        )
        decisions.append(decision)
        if decision.status in {"eligible", "speculative_only"}:
            allowlist.append(model.strategy_class)

    position_pct = min(float(limits["max_position_pct"]), float(inputs.max_loss_budget_pct))
    max_notional = float(inputs.bankroll) * max(position_pct, 0.001)
    min_notional = min((row.min_ticket_notional for row in strategy_models), default=1.0)

    acknowledgements: list[str] = []
    if mode == "speculative":
        acknowledgements.append("speculative_total_loss_risk_acknowledged")
        acknowledgements.append("preservation_language_suppressed")

    return CompiledCapitalPolicy(
        utility_mode=mode,
        strategy_allowlist=tuple(sorted(set(allowlist))),
        position_size_bounds={
            "min_notional": float(min_notional),
            "max_notional": float(max_notional),
        },
        concurrent_position_limit=max(int(round(float(limits["concurrent_positions"]))), 1),
        cadence_budget_per_day=max(int(round(float(limits["cadence_budget_per_day"]))), 1),
        drawdown_loss_envelope={
            "max_drawdown_pct": float(min(float(limits["drawdown_pct"]), float(inputs.max_loss_budget_pct))),
            "max_loss_budget_pct": float(inputs.max_loss_budget_pct),
            "max_loss_budget_notional": float(inputs.bankroll) * float(inputs.max_loss_budget_pct),
        },
        acknowledgements=tuple(acknowledgements),
        strategy_decisions=tuple(decisions),
    )
