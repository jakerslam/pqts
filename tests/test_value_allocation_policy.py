from __future__ import annotations

from risk.value_allocation_policy import (
    OpportunityCandidate,
    evaluate_conservative_value_range,
    evaluate_permanent_liquidity_reserve,
    rank_opportunity_cost_allocations,
)


def test_conservative_value_range_blocks_or_sizes_down() -> None:
    blocked = evaluate_conservative_value_range(
        market_price=0.60,
        conservative_value_low=0.58,
        conservative_value_high=0.72,
        cost_slippage_uncertainty_bps=60.0,
        required_margin_bps=25.0,
        sensitivity_drivers=["volatility", "oracle_delay"],
    )
    assert blocked.action == "block"
    assert "conservative_margin_non_positive" in blocked.reason_codes

    sized = evaluate_conservative_value_range(
        market_price=0.60,
        conservative_value_low=0.606,
        conservative_value_high=0.72,
        cost_slippage_uncertainty_bps=2.0,
        required_margin_bps=25.0,
        sensitivity_drivers=["volatility"],
    )
    assert sized.action in {"size_down", "allow"}


def test_opportunity_cost_ranking_and_liquidity_reserve() -> None:
    ranked = rank_opportunity_cost_allocations(
        opportunities=[
            OpportunityCandidate(
                strategy_id="s-low",
                expected_return=0.10,
                risk_penalty=0.03,
                liquidity_penalty=0.01,
                required_capital=500.0,
            ),
            OpportunityCandidate(
                strategy_id="s-best",
                expected_return=0.16,
                risk_penalty=0.04,
                liquidity_penalty=0.01,
                required_capital=600.0,
            ),
        ],
        available_capital=700.0,
    )
    assert ranked.deferred is False
    assert ranked.chosen_strategy_id == "s-best"

    reserve = evaluate_permanent_liquidity_reserve(
        total_liquidity=1_000.0,
        encumbered_liquidity=550.0,
        required_reserve_notional=500.0,
        projected_margin_demand=120.0,
        projected_collateral_demand=80.0,
        projected_settlement_demand=60.0,
        projected_rollback_demand=40.0,
    )
    assert reserve.reserve_breached is True
    assert reserve.halt_non_essential_expansion is True
    assert reserve.review_required is True
