from __future__ import annotations

from analytics.polymarket_assistant import (
    OrderBookSnapshot,
    TerminalDashboard,
    TrendAlertEngine,
    compute_indicators,
    fuse_orderflow_with_polymarket,
    trend_score,
    validate_asset_timeframe,
)


def test_indicator_stack_and_trend_score() -> None:
    snapshot = OrderBookSnapshot(bids=[(1.0, 200.0)], asks=[(1.1, 50.0)])
    indicators = compute_indicators(
        snapshot=snapshot,
        cvd=10.0,
        delta=5.0,
        volume_profile_poc=1.05,
        rsi=65.0,
        macd=0.2,
        vwap=1.02,
        ema_fast=1.03,
        ema_slow=1.01,
        heikin_ashi_trend="bullish",
        liquidity_band=1.0,
    )
    score = trend_score(indicators)
    assert score.state in {"bullish", "neutral"}


def test_fusion_and_terminal_dashboard() -> None:
    snapshot = OrderBookSnapshot(bids=[(1.0, 200.0)], asks=[(1.1, 50.0)])
    indicators = compute_indicators(
        snapshot=snapshot,
        cvd=10.0,
        delta=5.0,
        volume_profile_poc=1.05,
        rsi=65.0,
        macd=0.2,
        vwap=1.02,
        ema_fast=1.03,
        ema_slow=1.01,
        heikin_ashi_trend="bullish",
        liquidity_band=1.0,
    )
    score = trend_score(indicators)
    signal = fuse_orderflow_with_polymarket(trend=score, polymarket_price=0.55)
    dashboard = TerminalDashboard()
    output = dashboard.render(signal=signal, compact=True)
    assert "trend_state" in output


def test_trend_alert_engine_state_change() -> None:
    engine = TrendAlertEngine()
    snapshot = OrderBookSnapshot(bids=[(1.0, 200.0)], asks=[(1.1, 50.0)])
    indicators = compute_indicators(
        snapshot=snapshot,
        cvd=10.0,
        delta=5.0,
        volume_profile_poc=1.05,
        rsi=65.0,
        macd=0.2,
        vwap=1.02,
        ema_fast=1.03,
        ema_slow=1.01,
        heikin_ashi_trend="bullish",
        liquidity_band=1.0,
    )
    score = trend_score(indicators)
    alert = engine.check(trend=score, event_key="pmat")
    assert alert.reason in {"state_change", "extreme_state", "no_change"}


def test_supported_asset_matrix() -> None:
    assert validate_asset_timeframe("BTC", "5m")
    assert not validate_asset_timeframe("DOGE", "5m")
