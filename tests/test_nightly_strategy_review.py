from __future__ import annotations

from analytics.nightly_strategy_review import (
    NightlyReviewThresholds,
    apply_overrides_to_config,
    build_nightly_review,
)


def _base_config() -> dict:
    return {
        "execution": {
            "profitability_gate": {"min_edge_bps": 0.5},
            "paper_fill_model": {"stress_slippage_multiplier": 2.5},
        },
        "runtime": {"autopilot": {"max_active_strategies": 6}},
        "risk": {"daily_loss_limit": 500.0},
    }


def test_nightly_review_tightens_controls_when_metrics_degrade() -> None:
    snapshot = {
        "stats": {"reject_rate": 0.45, "filled": 40},
        "ops_health": {"summary": {"critical": 1, "warning": 2}},
        "revenue": {"summary": {"slippage_mape_pct": 31.0, "avg_realized_net_alpha_bps": -1.2}},
    }
    review = build_nightly_review(
        snapshot=snapshot,
        config=_base_config(),
        thresholds=NightlyReviewThresholds(
            max_reject_rate=0.30,
            max_slippage_mape_pct=25.0,
            min_realized_net_alpha_bps=0.0,
            max_critical_alerts=0,
        ),
    )
    deltas = review["deltas"]
    assert "execution.profitability_gate.min_edge_bps" in deltas
    assert deltas["execution.profitability_gate.min_edge_bps"]["after"] > 0.5
    assert "runtime.autopilot.max_active_strategies" in deltas
    assert deltas["runtime.autopilot.max_active_strategies"]["after"] < 6
    assert "execution.paper_fill_model.stress_slippage_multiplier" in deltas
    assert deltas["execution.paper_fill_model.stress_slippage_multiplier"]["after"] > 2.5


def test_nightly_review_relaxes_controls_when_metrics_are_healthy() -> None:
    snapshot = {
        "stats": {"reject_rate": 0.02, "filled": 500},
        "ops_health": {"summary": {"critical": 0, "warning": 0}},
        "revenue": {"summary": {"slippage_mape_pct": 4.0, "avg_realized_net_alpha_bps": 8.0}},
    }
    review = build_nightly_review(snapshot=snapshot, config=_base_config())
    deltas = review["deltas"]
    assert deltas["execution.profitability_gate.min_edge_bps"]["after"] < 0.5
    assert deltas["runtime.autopilot.max_active_strategies"]["after"] > 6
    assert any(action["rule"] == "healthy_relaxation" for action in review["actions"])


def test_apply_overrides_to_config_merges_nested_values() -> None:
    config = _base_config()
    overrides = {
        "execution": {"profitability_gate": {"min_edge_bps": 0.75}},
        "runtime": {"autopilot": {"max_active_strategies": 5}},
    }
    updated = apply_overrides_to_config(config=config, overrides=overrides)
    assert updated["execution"]["profitability_gate"]["min_edge_bps"] == 0.75
    assert updated["runtime"]["autopilot"]["max_active_strategies"] == 5
    assert updated["risk"]["daily_loss_limit"] == 500.0
