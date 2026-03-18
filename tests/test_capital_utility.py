from __future__ import annotations

import pytest

from risk.capital_utility import (
    CapitalUtilityInputs,
    StrategyCostModel,
    compile_bankroll_aware_policy,
    evaluate_fee_dominance,
    evaluate_min_efficient_capital,
)


def _model() -> StrategyCostModel:
    return StrategyCostModel(
        strategy_class="asymmetric_event",
        venue="polymarket",
        min_efficient_capital=500.0,
        min_ticket_notional=25.0,
        expected_edge_bps=45.0,
        fee_bps=10.0,
        slippage_bps=8.0,
        diversification_slots=3,
    )


def test_speculative_mode_requires_explicit_acknowledgement() -> None:
    inputs = CapitalUtilityInputs(
        bankroll=100.0,
        utility_mode="speculative",
        time_horizon_days=30,
        max_loss_budget_pct=0.80,
        speculative_acknowledged=False,
    )
    with pytest.raises(RuntimeError, match="requires explicit max-loss acknowledgement"):
        compile_bankroll_aware_policy(inputs=inputs, strategy_models=[_model()])


def test_min_efficient_capital_blocks_or_speculative_only() -> None:
    balanced = CapitalUtilityInputs(
        bankroll=120.0,
        utility_mode="balanced",
        time_horizon_days=30,
        max_loss_budget_pct=0.20,
    )
    blocked = evaluate_min_efficient_capital(inputs=balanced, model=_model())
    assert blocked.status == "blocked"
    assert "insufficient_efficient_capital" in blocked.drivers

    speculative = CapitalUtilityInputs(
        bankroll=120.0,
        utility_mode="speculative",
        time_horizon_days=14,
        max_loss_budget_pct=0.80,
        speculative_acknowledged=True,
    )
    override = evaluate_min_efficient_capital(inputs=speculative, model=_model())
    assert override.status == "speculative_only"
    assert "speculative_mode_override" in override.drivers


def test_fee_dominance_blocks_non_positive_after_cost_edge() -> None:
    decision = evaluate_fee_dominance(
        ticket_notional=20.0,
        expected_edge_bps=15.0,
        fee_bps=8.0,
        slippage_bps=10.0,
        min_efficient_ticket_notional=25.0,
    )
    assert decision.action == "block"
    assert decision.expected_after_cost_edge_bps <= 0.0
    assert "after_cost_edge_non_positive" in decision.reasons


def test_compile_policy_output_tracks_allowlist_and_envelope() -> None:
    inputs = CapitalUtilityInputs(
        bankroll=1_000.0,
        utility_mode="balanced",
        time_horizon_days=90,
        max_loss_budget_pct=0.25,
    )
    policy = compile_bankroll_aware_policy(
        inputs=inputs,
        strategy_models=[_model()],
    )
    payload = policy.as_dict()
    assert payload["utility_mode"] == "balanced"
    assert payload["strategy_allowlist"] == ["asymmetric_event"]
    assert payload["position_size_bounds"]["max_notional"] == pytest.approx(50.0)
    assert payload["drawdown_loss_envelope"]["max_loss_budget_notional"] == pytest.approx(250.0)
    assert payload["acknowledgements"] == []
