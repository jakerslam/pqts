"""Polymarket assistant signal fusion and terminal dashboard helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from analytics.notifications import NotificationDispatcher, NotificationChannels


@dataclass(frozen=True)
class OrderBookSnapshot:
    bids: list[tuple[float, float]]
    asks: list[tuple[float, float]]


@dataclass(frozen=True)
class IndicatorSet:
    imbalance: float
    buy_wall: bool
    sell_wall: bool
    liquidity_band: float
    cvd: float
    delta: float
    volume_profile_poc: float
    rsi: float
    macd: float
    vwap: float
    ema_fast: float
    ema_slow: float
    heikin_ashi_trend: str


@dataclass(frozen=True)
class TrendScore:
    score: float
    state: str
    reasons: list[str] = field(default_factory=list)


SUPPORTED_ASSET_MATRIX = {
    "BTC": ("5m", "15m", "1h", "4h", "1d"),
    "ETH": ("5m", "15m", "1h", "4h", "1d"),
    "SOL": ("5m", "15m", "1h", "4h", "1d"),
    "XRP": ("5m", "15m", "1h", "4h", "1d"),
}


def validate_asset_timeframe(asset: str, timeframe: str) -> bool:
    return str(timeframe) in SUPPORTED_ASSET_MATRIX.get(str(asset).upper(), ())


def _orderbook_imbalance(snapshot: OrderBookSnapshot) -> float:
    bid_vol = sum(size for _, size in snapshot.bids)
    ask_vol = sum(size for _, size in snapshot.asks)
    total = bid_vol + ask_vol
    if total <= 0:
        return 0.0
    return (bid_vol - ask_vol) / total


def _wall_detect(snapshot: OrderBookSnapshot, *, threshold: float = 100.0) -> tuple[bool, bool]:
    buy_wall = any(size >= threshold for _, size in snapshot.bids[:3])
    sell_wall = any(size >= threshold for _, size in snapshot.asks[:3])
    return buy_wall, sell_wall


def compute_indicators(
    *,
    snapshot: OrderBookSnapshot,
    cvd: float,
    delta: float,
    volume_profile_poc: float,
    rsi: float,
    macd: float,
    vwap: float,
    ema_fast: float,
    ema_slow: float,
    heikin_ashi_trend: str,
    liquidity_band: float = 0.0,
) -> IndicatorSet:
    imbalance = _orderbook_imbalance(snapshot)
    buy_wall, sell_wall = _wall_detect(snapshot)
    return IndicatorSet(
        imbalance=float(imbalance),
        buy_wall=buy_wall,
        sell_wall=sell_wall,
        liquidity_band=float(liquidity_band),
        cvd=float(cvd),
        delta=float(delta),
        volume_profile_poc=float(volume_profile_poc),
        rsi=float(rsi),
        macd=float(macd),
        vwap=float(vwap),
        ema_fast=float(ema_fast),
        ema_slow=float(ema_slow),
        heikin_ashi_trend=str(heikin_ashi_trend),
    )


def trend_score(indicators: IndicatorSet) -> TrendScore:
    score = 0.0
    reasons: list[str] = []

    if indicators.imbalance > 0.1:
        score += 0.2
        reasons.append("orderbook_imbalance_buy")
    elif indicators.imbalance < -0.1:
        score -= 0.2
        reasons.append("orderbook_imbalance_sell")

    if indicators.buy_wall:
        score += 0.1
        reasons.append("buy_wall")
    if indicators.sell_wall:
        score -= 0.1
        reasons.append("sell_wall")

    if indicators.cvd > 0:
        score += 0.1
        reasons.append("cvd_positive")
    elif indicators.cvd < 0:
        score -= 0.1
        reasons.append("cvd_negative")

    if indicators.rsi > 60:
        score += 0.1
        reasons.append("rsi_bullish")
    elif indicators.rsi < 40:
        score -= 0.1
        reasons.append("rsi_bearish")

    if indicators.macd > 0:
        score += 0.05
        reasons.append("macd_positive")
    elif indicators.macd < 0:
        score -= 0.05
        reasons.append("macd_negative")

    if indicators.ema_fast > indicators.ema_slow:
        score += 0.1
        reasons.append("ema_bullish")
    elif indicators.ema_fast < indicators.ema_slow:
        score -= 0.1
        reasons.append("ema_bearish")

    if indicators.heikin_ashi_trend.lower().startswith("bull"):
        score += 0.05
        reasons.append("ha_bullish")
    elif indicators.heikin_ashi_trend.lower().startswith("bear"):
        score -= 0.05
        reasons.append("ha_bearish")

    score = max(-1.0, min(1.0, score))
    state = "neutral"
    if score >= 0.2:
        state = "bullish"
    elif score <= -0.2:
        state = "bearish"
    return TrendScore(score=float(score), state=state, reasons=reasons)


@dataclass(frozen=True)
class FusionSignal:
    trend: TrendScore
    polymarket_price: float
    orderflow_bias: float
    confirmation: str


def fuse_orderflow_with_polymarket(
    *,
    trend: TrendScore,
    polymarket_price: float,
) -> FusionSignal:
    bias = trend.score
    confirmation = "neutral"
    if bias > 0.2 and polymarket_price < 0.5:
        confirmation = "contradiction"
    elif bias > 0.2 and polymarket_price >= 0.5:
        confirmation = "confirm"
    elif bias < -0.2 and polymarket_price > 0.5:
        confirmation = "contradiction"
    elif bias < -0.2 and polymarket_price <= 0.5:
        confirmation = "confirm"
    return FusionSignal(
        trend=trend,
        polymarket_price=float(polymarket_price),
        orderflow_bias=float(bias),
        confirmation=confirmation,
    )


class TerminalDashboard:
    def render(self, *, signal: FusionSignal, compact: bool = False) -> str:
        lines = [
            f"trend_state={signal.trend.state}",
            f"trend_score={signal.trend.score:.2f}",
            f"polymarket_price={signal.polymarket_price:.4f}",
            f"orderflow_bias={signal.orderflow_bias:.2f}",
            f"confirmation={signal.confirmation}",
        ]
        if not compact:
            lines.append(f"reasons={','.join(signal.trend.reasons)}")
        return "\n".join(lines)


@dataclass
class TrendAlert:
    state: str
    message: str
    dispatched: bool
    reason: str


class TrendAlertEngine:
    def __init__(self, *, dispatcher: NotificationDispatcher | None = None) -> None:
        self.dispatcher = dispatcher or NotificationDispatcher(NotificationChannels())
        self.last_state = "neutral"

    def check(
        self,
        *,
        trend: TrendScore,
        event_key: str,
        extreme_threshold: float = 0.8,
    ) -> TrendAlert:
        if trend.state != self.last_state:
            message = f"[PQTS TREND] state_change={self.last_state}->{trend.state}"
            result = self.dispatcher.dispatch(message, event_key=event_key)
            self.last_state = trend.state
            return TrendAlert(state=trend.state, message=message, dispatched=result.get("ok", False), reason="state_change")

        if abs(trend.score) >= extreme_threshold:
            message = f"[PQTS TREND] extreme_state={trend.state} score={trend.score:.2f}"
            result = self.dispatcher.dispatch(message, event_key=f"{event_key}:extreme")
            return TrendAlert(state=trend.state, message=message, dispatched=result.get("ok", False), reason="extreme_state")

        return TrendAlert(state=trend.state, message="no_alert", dispatched=False, reason="no_change")
