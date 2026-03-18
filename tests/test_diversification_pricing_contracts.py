from __future__ import annotations

from portfolio.diversification_pricing_contracts import (
    CohortQuality,
    detect_redundant_strategy_compression,
    enforce_bestseller_price_floor,
    enforce_discount_entry_offer_guardrail,
    evaluate_customer_fit_cohort_quality,
    evaluate_marginal_diversification_admission,
)


def test_ajo_pricing_and_cohort_guardrails() -> None:
    floor = enforce_bestseller_price_floor(
        bestseller_price=29.0,
        median_paid_price=100.0,
        min_bestseller_ratio=0.5,
        operator_id="op1",
        workspace_id="ws1",
    )
    assert floor.allowed is False
    assert floor.reason_code == "bestseller_ratio_below_floor"

    cohort_decision = evaluate_customer_fit_cohort_quality(
        cohorts=[
            CohortQuality("c-low", "low", 0.8, 0.5, 0.2, 0.03, 0.4, 0.1),
            CohortQuality("c-pro", "pro", 0.6, 0.5, 0.4, 0.15, 0.1, 0.35),
        ],
        min_retention_90d=0.30,
        min_upgrade_conversion=0.10,
        max_support_burden_rate=0.20,
        min_live_eligibility_attainment=0.20,
    )
    assert cohort_decision.warning is True
    assert cohort_decision.dominant_cohort_id == "c-low"

    discount = enforce_discount_entry_offer_guardrail(
        entry_price=9.0,
        policy_floor_price=19.0,
        has_success_criteria=False,
        has_auto_expiry=False,
        post_campaign_cohort_quality_ok=False,
    )
    assert discount.allowed is False
    assert discount.auto_disabled is True


def test_znm_diversification_admission_and_compression() -> None:
    admission = evaluate_marginal_diversification_admission(
        standalone_expectancy=0.08,
        standalone_risk_score=0.03,
        mean_correlation_to_active=0.9,
        expected_portfolio_impact=-0.01,
    )
    assert admission.allow_admission is False
    assert "high_correlation_to_active_portfolio" in admission.reason_codes

    compression = detect_redundant_strategy_compression(
        correlation_matrix={
            ("s1", "s2"): 0.92,
            ("s1", "s3"): 0.40,
            ("s2", "s3"): 0.35,
        },
        active_strategies={"s1", "s2", "s3"},
        redundancy_threshold=0.85,
    )
    assert len(compression.redundant_clusters) == 1
    assert "compress_cluster:s1,s2" in compression.recommended_actions
