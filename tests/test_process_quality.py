from __future__ import annotations

import pytest

from analytics.process_quality import (
    DecisionAdherenceEvent,
    build_fixed_rr_policy_receipt,
    compute_capital_efficiency_metrics,
    compute_strategy_adherence_score,
    detect_same_market_self_offset,
    evaluate_override_budget_and_drift_gate,
    evaluate_trade_count_vanity,
)


def test_adherence_score_and_override_budget_gate() -> None:
    events = [
        DecisionAdherenceEvent(
            strategy_id="s1",
            expected_entry_rule="ev_gt_0",
            expected_exit_rule="target_or_stop",
            expected_sizing_rule="kelly_25pct",
            observed_entry_rule="ev_gt_0",
            observed_exit_rule="target_or_stop",
            observed_sizing_rule="kelly_25pct",
        ),
        DecisionAdherenceEvent(
            strategy_id="s1",
            expected_entry_rule="ev_gt_0",
            expected_exit_rule="target_or_stop",
            expected_sizing_rule="kelly_25pct",
            observed_entry_rule="manual_override",
            observed_exit_rule="target_or_stop",
            observed_sizing_rule="manual_size",
            override_used=True,
            override_approved=False,
            override_severity=0.8,
        ),
    ]
    score = compute_strategy_adherence_score(events)
    assert score.strategy_id == "s1"
    assert score.unapproved_drift_rate == pytest.approx(0.5)
    decision = evaluate_override_budget_and_drift_gate(
        score=score,
        stage="live",
        max_override_rate=0.25,
        max_unapproved_drift_rate=0.10,
        max_mean_severity=0.40,
    )
    assert decision.allow_promotion is False
    assert decision.action == "kill-review"
    assert "unapproved_drift_exceeded" in decision.reason_codes


def test_fixed_rr_receipt_marks_mismatch_reason_codes() -> None:
    matched = build_fixed_rr_policy_receipt(
        strategy_id="s1",
        order_id="o1",
        declared_stop=0.42,
        declared_target=0.63,
        declared_invalidate="oracle_conflict",
        exit_price=0.63,
        exit_reason="target",
    )
    assert matched.policy_match is True
    assert matched.reason_code == "policy_matched"

    mismatched = build_fixed_rr_policy_receipt(
        strategy_id="s1",
        order_id="o2",
        declared_stop=0.42,
        declared_target=0.63,
        declared_invalidate="oracle_conflict",
        exit_price=0.51,
        exit_reason="discretionary_manual_close",
    )
    assert mismatched.policy_match is False
    assert mismatched.reason_code == "rr_policy_mismatch"


def test_capital_efficiency_self_offset_and_trade_count_vanity() -> None:
    candidate = compute_capital_efficiency_metrics(
        strategy_id="s1",
        net_pnl=20.0,
        locked_capital=50_000.0,
        order_count=80,
        turnover=300_000.0,
    )
    baseline = compute_capital_efficiency_metrics(
        strategy_id="baseline",
        net_pnl=60.0,
        locked_capital=50_000.0,
        order_count=20,
        turnover=80_000.0,
    )
    assert candidate.throughput_without_edge is True

    detection = detect_same_market_self_offset(
        strategy_id="s1",
        market_id="m1",
        side_sequence=["BUY", "SELL", "BUY", "SELL"],
        net_exposure=0.02,
        declared_two_sided_mode=False,
        expected_spread_capture=10.0,
        realized_spread_capture=2.0,
        window_start="2026-03-18T00:00:00+00:00",
        window_end="2026-03-18T01:00:00+00:00",
    )
    assert detection is not None
    assert detection.unexplained is True

    vanity = evaluate_trade_count_vanity(candidate=candidate, baseline=baseline)
    assert vanity.eligible_for_top_performer is False
    assert vanity.reason_code == "trade_count_vanity"
