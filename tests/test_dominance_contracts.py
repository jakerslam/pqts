from __future__ import annotations

from moat.dominance_contracts import (
    CompetitiveDimension,
    build_capital_governor_card,
    build_competitive_scorecard,
    build_conversion_report,
    build_trust_ops_dashboard_payload,
    create_hosted_sandbox_workspace,
    create_ops_job_receipt,
    evaluate_casual_convenience_moat,
    evaluate_casual_first_journey,
    evaluate_certified_prediction_market_scope,
    evaluate_connector_certification_depth,
    evaluate_constrained_operator_intelligence,
    evaluate_deployment_scenario_pack_coverage,
    evaluate_docs_troubleshooting_contract,
    evaluate_mobile_assistant_safety,
    evaluate_product_truth_availability,
    evaluate_release_maturity_transition,
    evaluate_rolling_proof_density,
    evaluate_tier1_venue_certification_depth,
    evaluate_truth_surface_gate,
    evaluate_verified_example_density,
)


def test_dom_scorecard_sandbox_certification_and_proof_density() -> None:
    scorecard = build_competitive_scorecard(
        [
            CompetitiveDimension("onboarding_speed", 0.82, 0.8, 0.6),
            CompetitiveDimension("certified_venues", 0.35, 0.8, 0.6),
        ]
    )
    assert scorecard.dimensions["onboarding_speed"] == "green"
    assert "certified_venues" in scorecard.weakest_dimensions

    sandbox = create_hosted_sandbox_workspace(
        workspace_id="ws1",
        bounded_capital_notional=250.0,
        ttl_hours=24,
    )
    assert sandbox.paper_safe_credentials is True
    assert sandbox.no_install_required is True

    cert = evaluate_tier1_venue_certification_depth(
        venue="polymarket",
        has_paper=True,
        has_canary=True,
        has_live_readiness=False,
        has_30d_evidence=True,
        has_90d_evidence=True,
    )
    assert cert.eligible_for_stage is False
    assert "missing_live_readiness" in cert.reason_codes

    density = evaluate_rolling_proof_density(
        strategy_count=3,
        venue_count=2,
        regime_count=2,
        monthly_bundle_count=8,
    )
    assert density.complete is False


def test_dom_docs_examples_truth_and_connector_depth() -> None:
    docs = evaluate_docs_troubleshooting_contract(
        searchable_docs_enabled=True,
        drift_checks_pass=False,
        metadata_fresh=True,
    )
    assert docs.healthy is False
    examples = evaluate_verified_example_density(verified_example_count=10, required_minimum=12)
    assert examples.meets_density is False

    truth = evaluate_truth_surface_gate(
        readme_ok=True,
        pypi_ok=True,
        docs_ok=True,
        release_notes_ok=False,
    )
    assert truth.pass_gate is False

    connector = evaluate_connector_certification_depth(
        connector_status="beta",
        paper_ok=True,
        canary_ok=True,
        live_ok=True,
        reliability_budget_ok=True,
    )
    assert connector.pass_gate is False

    conversion = build_conversion_report(
        hosted_conversion=0.3,
        local_conversion=0.2,
        beginner_conversion=0.25,
        professional_conversion=0.4,
    )
    assert conversion.professional_conversion > conversion.beginner_conversion
    dashboard = build_trust_ops_dashboard_payload(
        release_readiness="green",
        benchmark_freshness="yellow",
        venue_certification="red",
        docs_freshness="green",
        package_availability="green",
    )
    assert dashboard.venue_certification == "red"


def test_dom_ops_capital_safety_and_maturity_controls() -> None:
    job = create_ops_job_receipt(
        job_id="nightly-review",
        status="running",
        artifacts=["artifact://nightly/1"],
        retries=1,
        approval_required=True,
    )
    assert job.approval_required is True

    card = build_capital_governor_card(
        strategy_id="s1",
        trust_label="verified",
        promotion_stage="canary",
        venue_compatibility=["polymarket"],
        drawdown_envelope=0.15,
        reject_fill_slippage_score=0.8,
        correlation_budget_score=0.4,
        recommended_capital_budget=1000.0,
    )
    assert card.recommended_capital_budget == 1000.0

    mobile = evaluate_mobile_assistant_safety(
        rbac_ok=True,
        audit_trail_ok=True,
        confirmation_required=False,
        assistant_action_kind="execute",
    )
    assert mobile.allowed is False

    packs = evaluate_deployment_scenario_pack_coverage(
        has_fee_regimes=True,
        has_reconnect_outage=True,
        has_settlement_oracle_lag=False,
        has_cross_market_skew=True,
    )
    assert packs.complete is False

    maturity = evaluate_release_maturity_transition(
        current_state="alpha",
        target_state="beta",
        evidence_pack_present=True,
        benchmark_ok=True,
        docs_ok=True,
    )
    assert maturity.allowed_transition is True

    casual = evaluate_casual_first_journey(
        primary_screen_count=3,
        advanced_hidden_by_default=True,
        parity_objects_shared=True,
    )
    assert casual.valid is True

    operator = evaluate_constrained_operator_intelligence(
        memo_artifact_refs=["artifact://memo/1"],
        privileged_execution_requested=True,
        operator_approved=False,
    )
    assert operator.execute_allowed is False

    scope = evaluate_certified_prediction_market_scope(
        market_type="prediction_market",
        connector_certified=False,
        stage="live",
    )
    assert scope.allowed is False

    availability = evaluate_product_truth_availability(
        readme_links_ok=True,
        docs_links_ok=True,
        release_links_ok=True,
        pypi_links_ok=True,
        metric_parity_ok=False,
    )
    assert availability.pass_gate is False

    moat = evaluate_casual_convenience_moat(
        mobile_notifications_available=True,
        governed_approval_inbox_available=True,
        incident_review_mobile_available=True,
        rbac_audit_ok=True,
    )
    assert moat.competitive is True
