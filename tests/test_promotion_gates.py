"""Deterministic tests for 30-90 day promotion gate logic."""

from __future__ import annotations

from analytics.promotion_gates import PromotionGateThresholds, evaluate_promotion_gate


def test_promotion_gate_promotes_when_all_conditions_pass():
    result = evaluate_promotion_gate(
        readiness={
            "trading_days": 45,
            "fills": 500,
            "ready_for_canary": True,
        },
        campaign_stats={"reject_rate": 0.05},
        ops_summary={"critical": 0},
        thresholds=PromotionGateThresholds(
            min_days=30,
            max_days=90,
            min_fills=200,
            max_reject_rate=0.40,
            max_critical_alerts=0,
        ),
    )
    assert result["decision"] == "promote_to_live_canary"
    assert all(result["checks"].values())


def test_promotion_gate_rejects_after_window_if_not_ready():
    result = evaluate_promotion_gate(
        readiness={
            "trading_days": 120,
            "fills": 1000,
            "ready_for_canary": False,
        },
        campaign_stats={"reject_rate": 0.02},
        ops_summary={"critical": 0},
        thresholds=PromotionGateThresholds(),
    )
    assert result["decision"] == "reject_or_research"
    assert result["checks"]["max_days_window"] is False


def test_promotion_gate_stays_in_paper_on_critical_alerts():
    result = evaluate_promotion_gate(
        readiness={
            "trading_days": 40,
            "fills": 400,
            "ready_for_canary": True,
        },
        campaign_stats={"reject_rate": 0.10},
        ops_summary={"critical": 1},
        thresholds=PromotionGateThresholds(max_critical_alerts=0),
    )
    assert result["decision"] == "remain_in_paper"
    assert result["checks"]["critical_alerts"] is False
