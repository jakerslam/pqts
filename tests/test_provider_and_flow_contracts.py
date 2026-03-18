from __future__ import annotations

from analytics.provider_and_flow_contracts import (
    ForecasterPrediction,
    LiquidationPressurePoint,
    ProbabilityBandAttribution,
    ReadOnlyToolCapability,
    build_liquidation_pressure_surface,
    build_tool_surface_response,
    compute_feedback_velocity_metrics,
    detect_trade_count_volume_illusion,
    evaluate_adaptive_vs_static_baseline,
    evaluate_delay_adjusted_provider_consumption,
    evaluate_multi_venue_flow_confirmation,
    evaluate_probability_band_specialization,
    ingest_sponsored_claim,
    register_read_only_tool_surface,
    score_external_forecaster,
    validate_tool_registry_parity,
)


def test_sams_scoring_and_delay_adjusted_consumption() -> None:
    score = score_external_forecaster(
        [
            ForecasterPrediction("f1", "sports", 0.70, 1, "2026-03-18T00:00:00+00:00", "winner", "24h", 500),
            ForecasterPrediction("f1", "sports", 0.40, 0, "2026-03-18T00:00:00+00:00", "winner", "24h", 500),
        ]
    )
    assert score.sample_count == 2
    delayed = evaluate_delay_adjusted_provider_consumption(
        pre_delay_edge_bps=12.0,
        post_delay_edge_bps=1.0,
        min_post_delay_edge_bps=2.0,
    )
    assert delayed.action in {"down_weight", "shadow_only"}
    assert len(delayed.reason_codes) >= 1


def test_sfd_dfmi_and_ashc_contracts() -> None:
    velocity = compute_feedback_velocity_metrics(
        market_class="short_cycle",
        median_time_to_label_hours=2.0,
        episodes_per_day=30.0,
        train_cycle_hours=4.0,
    )
    assert velocity.velocity_score > 0.0
    adaptive = evaluate_adaptive_vs_static_baseline(
        adaptive_net_edge_bps=3.0,
        static_net_edge_bps=2.5,
        parity_assumptions_ok=False,
        min_lift_bps=1.0,
    )
    assert adaptive.allow_promotion is False

    surface = build_liquidation_pressure_surface(
        [
            LiquidationPressurePoint("62k-63k", 0.8, "down", "liq.v1", "2026-03-18T00:00:00+00:00"),
        ]
    )
    assert len(surface["points"]) == 1
    flow = evaluate_multi_venue_flow_confirmation(
        venue_votes={"binance": True, "coinbase": False},
        noise_filters_rejected=["single_print_spike"],
        min_agreement_ratio=0.75,
    )
    assert flow.action == "down_rank"

    claim = ingest_sponsored_claim(
        claim_id="c1",
        source_url="https://x.com/example/1",
        sponsored_claim=True,
    )
    assert claim.trust_label == "sponsored_claim"
    band = evaluate_probability_band_specialization(
        claimed_bands={"30-40"},
        observed=[ProbabilityBandAttribution("30-40", 20, 0.01, 0.05, 8.0)],
        min_samples_per_band=25,
        min_net_expectancy=0.02,
    )
    assert band.allow_promotion is False
    warning = detect_trade_count_volume_illusion(
        turnover_adjusted_alpha=-0.01,
        top_outcome_contribution_ratio=0.8,
    )
    assert warning.warn is True


def test_qsci_read_only_tool_surface_contracts() -> None:
    capability = ReadOnlyToolCapability(
        tool_id="market_data_quotes",
        asset_classes=("equities",),
        fields=("price", "volume"),
        granularity="1m",
        entitlement_requirement="pro_feed",
        freshness_posture="real_time",
        coverage_gaps=("options_iv",),
        read_only=True,
    )
    register_read_only_tool_surface(capability)

    response = build_tool_surface_response(
        provider_identity="polygon",
        as_of_timestamp="2026-03-18T00:00:00+00:00",
        schema_version="v2",
        permission_scope="workspace:read",
        payload={"symbol": "AAPL", "price": 210.0},
        provider_state="degraded",
        in_declared_coverage=True,
    )
    assert response.ok is False
    assert "provider_degraded" in response.reason_codes

    assert (
        validate_tool_registry_parity(
            tool_capability_ids={"polygon", "fmp"},
            canonical_connector_ids={"polygon", "fmp"},
        )
        is True
    )
