"""Conservative value-range, opportunity-cost allocation, and liquidity reserve policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConservativeValueDecision:
    action: str
    conservative_margin_bps: float
    sensitivity_drivers: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "conservative_margin_bps": float(self.conservative_margin_bps),
            "sensitivity_drivers": list(self.sensitivity_drivers),
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class OpportunityCandidate:
    strategy_id: str
    expected_return: float
    risk_penalty: float
    liquidity_penalty: float
    required_capital: float

    def __post_init__(self) -> None:
        if not str(self.strategy_id).strip():
            raise ValueError("strategy_id is required")
        if float(self.required_capital) <= 0.0:
            raise ValueError("required_capital must be > 0")


@dataclass(frozen=True)
class OpportunityAllocationDecision:
    chosen_strategy_id: str | None
    deferred: bool
    ranked_strategy_ids: tuple[str, ...]
    rationale: str
    rejected_alternatives: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "chosen_strategy_id": self.chosen_strategy_id,
            "deferred": bool(self.deferred),
            "ranked_strategy_ids": list(self.ranked_strategy_ids),
            "rationale": self.rationale,
            "rejected_alternatives": list(self.rejected_alternatives),
        }


@dataclass(frozen=True)
class LiquidityReserveDecision:
    reserve_ratio: float
    reserve_breached: bool
    halt_non_essential_expansion: bool
    post_shock_liquidity: float
    review_required: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "reserve_ratio": float(self.reserve_ratio),
            "reserve_breached": bool(self.reserve_breached),
            "halt_non_essential_expansion": bool(self.halt_non_essential_expansion),
            "post_shock_liquidity": float(self.post_shock_liquidity),
            "review_required": bool(self.review_required),
        }


def evaluate_conservative_value_range(
    *,
    market_price: float,
    conservative_value_low: float,
    conservative_value_high: float,
    cost_slippage_uncertainty_bps: float,
    required_margin_bps: float,
    sensitivity_drivers: list[str],
) -> ConservativeValueDecision:
    """Down-size or block when conservative value range loses required margin."""

    if float(conservative_value_low) <= 0.0 or float(conservative_value_high) <= 0.0:
        raise ValueError("value range must be positive")
    if float(conservative_value_low) > float(conservative_value_high):
        raise ValueError("conservative_value_low must be <= conservative_value_high")
    if float(market_price) <= 0.0:
        raise ValueError("market_price must be > 0")

    raw_margin_bps = ((float(conservative_value_low) - float(market_price)) / float(market_price)) * 10_000.0
    conservative_margin_bps = raw_margin_bps - float(cost_slippage_uncertainty_bps)
    reasons: list[str] = []
    action = "allow"
    if conservative_margin_bps <= 0.0:
        action = "block"
        reasons.append("conservative_margin_non_positive")
    elif conservative_margin_bps < float(required_margin_bps):
        action = "size_down"
        reasons.append("conservative_margin_below_required_buffer")
    return ConservativeValueDecision(
        action=action,
        conservative_margin_bps=conservative_margin_bps,
        sensitivity_drivers=tuple(sorted(set(str(x).strip() for x in sensitivity_drivers if str(x).strip()))),
        reason_codes=tuple(sorted(set(reasons))),
    )


def rank_opportunity_cost_allocations(
    *,
    opportunities: list[OpportunityCandidate],
    available_capital: float,
) -> OpportunityAllocationDecision:
    """Rank opportunities by risk/liquidity-aware incremental contribution."""

    if not opportunities:
        return OpportunityAllocationDecision(
            chosen_strategy_id=None,
            deferred=True,
            ranked_strategy_ids=(),
            rationale="no_opportunities",
            rejected_alternatives=(),
        )

    scored = sorted(
        opportunities,
        key=lambda row: (
            float(row.expected_return) - float(row.risk_penalty) - float(row.liquidity_penalty),
            -float(row.required_capital),
        ),
        reverse=True,
    )
    ranked = tuple(row.strategy_id for row in scored)
    chosen = scored[0]
    if float(chosen.required_capital) > float(available_capital):
        return OpportunityAllocationDecision(
            chosen_strategy_id=None,
            deferred=True,
            ranked_strategy_ids=ranked,
            rationale="retain_capital_insufficient_for_top_opportunity",
            rejected_alternatives=ranked,
        )
    return OpportunityAllocationDecision(
        chosen_strategy_id=chosen.strategy_id,
        deferred=False,
        ranked_strategy_ids=ranked,
        rationale="selected_highest_incremental_value",
        rejected_alternatives=tuple(x for x in ranked if x != chosen.strategy_id),
    )


def evaluate_permanent_liquidity_reserve(
    *,
    total_liquidity: float,
    encumbered_liquidity: float,
    required_reserve_notional: float,
    projected_margin_demand: float,
    projected_collateral_demand: float,
    projected_settlement_demand: float,
    projected_rollback_demand: float,
) -> LiquidityReserveDecision:
    """Maintain unencumbered reserve and report post-shock liquidity."""

    free_liquidity = float(total_liquidity) - float(encumbered_liquidity)
    total_shock = (
        float(projected_margin_demand)
        + float(projected_collateral_demand)
        + float(projected_settlement_demand)
        + float(projected_rollback_demand)
    )
    post_shock = free_liquidity - total_shock
    reserve_ratio = free_liquidity / max(float(required_reserve_notional), 1e-9)
    reserve_breached = free_liquidity < float(required_reserve_notional)
    return LiquidityReserveDecision(
        reserve_ratio=reserve_ratio,
        reserve_breached=reserve_breached,
        halt_non_essential_expansion=reserve_breached,
        post_shock_liquidity=post_shock,
        review_required=reserve_breached or post_shock < 0.0,
    )
