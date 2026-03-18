from __future__ import annotations

from execution.strategy_family_contracts import (
    ForecastSource,
    MicroLadderState,
    NearEvenMarketCandidate,
    TimeframeSignal,
    build_proxy_contract_advisory_decomposition,
    choose_forecast_source_tier,
    classify_copyability_label,
    enforce_forecast_only_signal_purity,
    evaluate_event_time_blackout,
    evaluate_market_class_fit,
    evaluate_micro_edge_exit,
    evaluate_multitimeframe_conflict,
    evaluate_passive_only_fill,
    select_near_even_markets,
    update_micro_lot_ladder,
)


def test_rvx_near_even_passive_ladder_and_blackout_controls() -> None:
    selected = select_near_even_markets(
        candidates=[
            NearEvenMarketCandidate(
                market_id="m1",
                price=0.50,
                fee_adjusted_spread_bps=4.0,
                resting_depth=2000.0,
                event_start_ts="2099-01-01T01:00:00+00:00",
                quote_staleness_ms=200,
            ),
            NearEvenMarketCandidate(
                market_id="m2",
                price=0.60,
                fee_adjusted_spread_bps=1.0,
                resting_depth=100.0,
                event_start_ts="2099-01-01T01:00:00+00:00",
                quote_staleness_ms=6_000,
            ),
        ]
    )
    assert selected[0].market_id == "m1"
    assert selected[0].eligible is True
    assert selected[1].eligible is False

    passive = evaluate_passive_only_fill(passive_fill=False, policy_override_enabled=False)
    assert passive.reason_code == "aggressive_fill_policy_violation"

    ladder = update_micro_lot_ladder(
        state=MicroLadderState({}, {}, {}, 0.0, ()),
        level="0.50",
        filled_qty=20.0,
        side="BUY",
        per_side_inventory_cap=10.0,
    )
    assert abs(ladder.net_inventory) == 10.0
    assert "inventory_cap_rebalance" in ladder.rebalance_actions

    blackout = evaluate_event_time_blackout(
        now_ts="2099-01-01T00:55:00+00:00",
        event_start_ts="2099-01-01T01:00:00+00:00",
        settlement_ts="2099-01-01T02:00:00+00:00",
        inventory_open=True,
        pre_start_blackout_minutes=10,
        in_play_blackout_enabled=True,
        settlement_blackout_minutes=5,
        hedging_active=False,
        explicit_reapproval=False,
    )
    assert blackout.action == "flatten"


def test_rvx_copyability_and_exit_logic() -> None:
    label = classify_copyability_label(
        latency_sensitive=True,
        queue_position_sensitive=True,
        fill_decay_half_life_seconds=8,
    )
    assert label.label == "non_copyable"

    exit_decision = evaluate_micro_edge_exit(
        expected_edge_bps=1.0,
        tick_target_hit=False,
        mean_reversion_hit=False,
        max_hold_timeout_hit=False,
        time_to_event_seconds=500,
        edge_decay_threshold_bps=2.0,
    )
    assert exit_decision.action in {"reduce", "flatten"}


def test_pwx_krl_and_sols_contracts() -> None:
    purity = enforce_forecast_only_signal_purity(
        forecast_only=True,
        input_classes=["forecast_model", "social_feed"],
        allowed_forecast_inputs={"forecast_model", "agency_feed"},
        explicit_override=False,
    )
    assert purity.allow_trade is False

    source_decision = choose_forecast_source_tier(
        sources=[
            ForecastSource("consumer", "consumer_summary", 5_000, 0.7),
            ForecastSource("direct", "direct_model", 2_000, 0.8),
        ],
        require_direct_model_edge=True,
    )
    assert source_decision.selected_source_id == "direct"

    fit = evaluate_market_class_fit(
        declared_market_classes={"sports", "politics"},
        target_market_class="macro",
        has_class_priors=False,
        has_class_calibration=False,
        has_exec_quality_evidence=False,
    )
    assert fit.allow_class is False
    assert "undeclared_market_class" in fit.reason_codes

    advisory = build_proxy_contract_advisory_decomposition(
        target_contract="poly://mkt/1",
        proxy_venue="binance",
        proxy_flow_weight=0.6,
        target_market_weight=0.3,
        technical_weight=0.1,
        freshness_ms=2000,
    )
    assert advisory.read_only is True

    conflict = evaluate_multitimeframe_conflict(
        signals=[
            TimeframeSignal("1m", "up", 0.55, 500),
            TimeframeSignal("15m", "down", 0.52, 1200),
        ],
        conflict_threshold=0.35,
    )
    assert conflict.conflict is True
