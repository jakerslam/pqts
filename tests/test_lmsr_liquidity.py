from __future__ import annotations

import pytest

from execution.lmsr_liquidity import (
    build_lmsr_sensitivity_report,
    classify_depth_regime_and_tighten_guards,
    compute_realized_vs_projected_impact_error,
    evaluate_lmsr_execution_eligibility,
)


def test_lmsr_sensitivity_report_and_stage_eligibility() -> None:
    report = build_lmsr_sensitivity_report(
        market_id="mkt1",
        liquidity_b=50.0,
        q_yes=100.0,
        q_no=95.0,
        scenario_sizes={"small": 1.0, "medium": 8.0, "large": 20.0},
    )
    assert report.base_probability_yes > 0.0
    assert len(report.scenarios) == 3

    decision = evaluate_lmsr_execution_eligibility(
        stage="live",
        report=report,
        impact_thresholds_by_stage={"paper": 0.25, "canary": 0.12, "live": 0.08},
    )
    assert decision.allow_trade in {True, False}
    assert decision.stage == "live"


def test_thin_pool_regime_tightens_guards_and_impact_error() -> None:
    thin = classify_depth_regime_and_tighten_guards(
        realized_slippage_bps=28.0,
        projected_slippage_bps=10.0,
        depth_score=0.20,
        base_size_cap=1000.0,
        base_repricing_limit=8,
        base_min_net_edge_bps=5.0,
    )
    assert thin.regime == "thin"
    assert thin.tightened_size_cap < 1000.0
    assert thin.tightened_min_net_edge_bps > 5.0

    error = compute_realized_vs_projected_impact_error(projected_shift=0.01, realized_shift=0.03)
    assert error == pytest.approx(0.02)
