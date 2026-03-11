from __future__ import annotations

import pytest

from strategies.short_cycle_rcg import (
    ClaimablePosition,
    MarketDiscoveryInput,
    ReferencePriceSample,
    SettlementWorker,
    build_dry_run_parity_artifact,
    build_reference_price_context,
    choose_maker_first_style,
    decide_dynamic_repricing,
    discover_markets,
    evaluate_beginner_validation_ladder,
    evaluate_complementary_bundle_edge,
)


def test_discover_markets_fail_closed_on_ambiguous_assets() -> None:
    resolved, errors = discover_markets(
        rows=[
            MarketDiscoveryInput(
                market_id="m1",
                asset_candidates=("BTC", "ETH"),
                interval_candidates=("5m",),
                yes_token="y1",
                no_token="n1",
            ),
            MarketDiscoveryInput(
                market_id="m2",
                asset_candidates=("BTC",),
                interval_candidates=("5m",),
                yes_token="y2",
                no_token="n2",
            ),
        ],
        allowed_assets=("BTC", "ETH"),
        allowed_intervals=("5m", "15m"),
    )
    assert len(resolved) == 1
    assert resolved[0].market_id == "m2"
    assert "m1:asset_resolution_failed" in errors


def test_dry_run_parity_artifact_emits_block_reason() -> None:
    artifact = build_dry_run_parity_artifact(
        market_id="m1",
        expected_edge_bps=-1.0,
        liquidity_score=0.9,
        risk_passed=True,
    )
    assert artifact.would_submit is False
    assert artifact.would_fill is False
    assert artifact.why_blocked == "expected_edge_non_positive"


def test_complementary_bundle_edge_gate_applies_fee_realism() -> None:
    diag = evaluate_complementary_bundle_edge(
        ask_yes=0.48,
        ask_no=0.48,
        maker_fee_bps=4.0,
        taker_fee_bps=12.0,
        use_maker=False,
        slippage_bps=2.0,
        residual_risk_bps=1.0,
        min_required_bps=5.0,
    )
    assert diag.fee_bps == 12.0
    assert diag.gross_edge_bps == pytest.approx(400.0)
    assert diag.net_edge_bps == pytest.approx(385.0)
    assert diag.passed is True


def test_dynamic_repricing_decision_reprices_stale_quote() -> None:
    decision = decide_dynamic_repricing(
        side="buy",
        current_limit_price=0.49,
        best_bid=0.52,
        best_ask=0.53,
        now_ms=10_000,
        last_quote_ms=1_000,
        max_quote_lifetime_ms=2_000,
        min_tick=0.0001,
        replace_count=0,
        max_replace_count=3,
    )
    assert decision.action == "reprice"
    assert decision.new_limit_price == 0.52
    assert decision.reason == "stale_quote"


def test_maker_first_policy_falls_back_when_urgent() -> None:
    decision = choose_maker_first_style(
        maker_first_enabled=True,
        taker_fallback_enabled=True,
        urgency_score=0.95,
        elapsed_wait_ms=5000,
        max_maker_wait_ms=2000,
    )
    assert decision.order_style == "ioc"
    assert decision.fallback_used is True


def test_reference_price_context_blocks_divergent_sources() -> None:
    context = build_reference_price_context(
        samples=[
            ReferencePriceSample(source="a", price=100.0, timestamp_ms=10_000, priority=1),
            ReferencePriceSample(source="b", price=103.5, timestamp_ms=10_000, priority=2),
        ],
        now_ms=11_000,
        max_age_ms=10_000,
        max_divergence_bps=200.0,
    )
    assert context.selected_source == "a"
    assert context.passed is False
    assert context.reason == "divergence_exceeded"


def test_beginner_validation_ladder_surfaces_first_failed_step() -> None:
    summary = evaluate_beginner_validation_ladder(
        {
            "market_discovery": True,
            "dry_run_parity": False,
            "edge_gate": False,
            "risk_guardrails": True,
            "settlement_ready": True,
        }
    )
    assert summary["passed"] is False
    assert summary["first_failed_step"] == "dry_run_parity"
    assert "would_submit" in str(summary["next_action"])


def test_settlement_worker_retries_and_is_idempotent() -> None:
    worker = SettlementWorker(max_retries=3, backoff_seconds=0.0)
    calls: dict[str, int] = {}

    def redeem_fn(position: ClaimablePosition) -> tuple[bool, str]:
        count = calls.get(position.position_id, 0) + 1
        calls[position.position_id] = count
        if count < 2:
            return False, "temporary_error"
        return True, "ok"

    attempts_first = worker.process_claimable_positions(
        positions=[
            ClaimablePosition(position_id="p1", market_id="m1", claimable=True, notional_usd=42.0),
        ],
        redeem_fn=redeem_fn,
    )
    assert len(attempts_first) == 2
    assert attempts_first[-1].ok is True
    attempts_second = worker.process_claimable_positions(
        positions=[
            ClaimablePosition(position_id="p1", market_id="m1", claimable=True, notional_usd=42.0),
        ],
        redeem_fn=redeem_fn,
    )
    assert len(attempts_second) == 1
    assert attempts_second[0].reason == "already_redeemed"
