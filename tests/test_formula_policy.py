from __future__ import annotations

import pytest

from execution.formula_policy import (
    FormulaDrivenManifest,
    FormulaSpec,
    build_context_sync_receipt,
    build_formula_decision_receipt,
    compile_formula_manifest_to_policy,
    evaluate_copy_logic_stage_bounded_eligibility,
    evaluate_correlated_market_divergence,
    evaluate_short_horizon_freshness,
)


def test_formula_manifest_compile_and_receipt() -> None:
    manifest = FormulaDrivenManifest(
        strategy_id="mvz_strategy",
        version="v1",
        formulas=(
            FormulaSpec(formula_id="f1", kind="bayesian_update", expression="p_post = ..."),
            FormulaSpec(formula_id="f2", kind="ev_gate", expression="edge_bps > 5"),
        ),
        risk_bounds={"max_position_pct": 0.05, "max_daily_loss_pct": 0.02},
        stage_constraints=("backtest", "paper", "shadow"),
    )
    compiled = compile_formula_manifest_to_policy(manifest)
    assert compiled.compiled_version == "v1.compiled"
    receipt = build_formula_decision_receipt(
        strategy_id="mvz_strategy",
        decision_id="d1",
        manifest_version=compiled.source_manifest_version,
        formula_inputs={"p_market": 0.44, "p_model": 0.51},
        formula_outputs={"edge_bps": 18.0},
    )
    assert receipt.formula_outputs["edge_bps"] == pytest.approx(18.0)


def test_divergence_and_freshness_gates() -> None:
    blocked = evaluate_correlated_market_divergence(
        divergence_metric=0.05,
        expected_net_edge_bps=2.0,
        min_divergence=0.10,
        min_net_edge_bps=5.0,
    )
    assert blocked.allow_trade is False
    assert "divergence_below_threshold" in blocked.reason_codes
    assert "net_edge_below_threshold" in blocked.reason_codes

    fresh = evaluate_short_horizon_freshness(
        signal_age_ms=18_000,
        time_left_seconds=20,
        max_signal_age_ms=15_000,
        min_time_left_seconds=30,
    )
    assert fresh.allow_trade is False
    assert "signal_age_exceeded" in fresh.reason_codes
    assert "insufficient_time_left" in fresh.reason_codes


def test_context_sync_and_copy_logic_stage_bounds() -> None:
    sync = build_context_sync_receipt(
        origin_surface="assistant",
        requested_action="execute",
        config_version="cfg.v9",
        eligibility_state="paper_only",
        conflict_detected=False,
    )
    assert sync.resolved_action == "propose"

    conflict = build_context_sync_receipt(
        origin_surface="terminal",
        requested_action="execute",
        config_version="cfg.v9",
        eligibility_state="eligible",
        conflict_detected=True,
    )
    assert conflict.resolved_action == "hold"

    blocked = evaluate_copy_logic_stage_bounded_eligibility(
        stage="live",
        prior_stage="paper",
        leader_id="leader-1",
        allowed_leaders={"leader-1"},
        requested_notional=300.0,
        per_source_notional_cap=200.0,
        router_path_enforced=True,
        gate_evaluators_passed=True,
    )
    assert blocked.eligible is False
    assert "stage_skip_not_allowed" in blocked.reason_codes
    assert "per_source_risk_cap_exceeded" in blocked.reason_codes
