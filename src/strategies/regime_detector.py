"""Compatibility regime detector facade for strategy-layer callers.

Canonical detector logic lives in `research.regime_detector`.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict

import pandas as pd

from research.regime_detector import MarketRegime as ResearchRegime
from research.regime_detector import RegimeDetector as ResearchRegimeDetector

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    LOW_VOLATILITY = "low_volatility"


_REGIME_MAP: dict[ResearchRegime, MarketRegime] = {
    ResearchRegime.TREND_UP: MarketRegime.TRENDING_UP,
    ResearchRegime.TREND_DOWN: MarketRegime.TRENDING_DOWN,
    ResearchRegime.MEAN_REVERSION: MarketRegime.RANGING,
    ResearchRegime.RANGE_BOUND: MarketRegime.RANGING,
    ResearchRegime.HIGH_VOLATILITY: MarketRegime.VOLATILE,
    ResearchRegime.LOW_LIQUIDITY: MarketRegime.LOW_VOLATILITY,
    ResearchRegime.HIGH_LIQUIDITY: MarketRegime.LOW_VOLATILITY,
}


class RegimeDetector:
    """Thin adapter preserving legacy strategy-layer API shape."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._impl = ResearchRegimeDetector(self.config)
        self.current_regime = MarketRegime.RANGING
        self.regime_history: list[dict[str, object]] = []
        logger.info("RegimeDetector compatibility wrapper initialized")

    def detect_regime(self, df: pd.DataFrame) -> MarketRegime:
        if df is None or len(df) == 0:
            return self.current_regime
        base_regime, scores = self._impl.detect_regime(df)
        mapped = _REGIME_MAP.get(base_regime, MarketRegime.RANGING)
        self.current_regime = mapped
        self.regime_history.append(
            {
                "timestamp": df.index[-1],
                "regime": mapped.value,
                "confidence": float(scores.get("overall", 0.0)),
            }
        )
        if len(self.regime_history) > 200:
            self.regime_history = self.regime_history[-200:]
        return mapped

    def get_strategy_params(self, regime: MarketRegime) -> Dict:
        params = {
            MarketRegime.TRENDING_UP: {
                "trend_following_weight": 1.0,
                "mean_reversion_weight": 0.0,
                "scalping_weight": 0.3,
                "position_size_multiplier": 1.2,
            },
            MarketRegime.TRENDING_DOWN: {
                "trend_following_weight": 1.0,
                "mean_reversion_weight": 0.0,
                "scalping_weight": 0.2,
                "position_size_multiplier": 0.8,
            },
            MarketRegime.RANGING: {
                "trend_following_weight": 0.0,
                "mean_reversion_weight": 1.0,
                "scalping_weight": 0.8,
                "position_size_multiplier": 1.0,
            },
            MarketRegime.VOLATILE: {
                "trend_following_weight": 0.3,
                "mean_reversion_weight": 0.5,
                "scalping_weight": 0.2,
                "position_size_multiplier": 0.5,
            },
            MarketRegime.LOW_VOLATILITY: {
                "trend_following_weight": 0.2,
                "mean_reversion_weight": 0.4,
                "scalping_weight": 1.0,
                "position_size_multiplier": 1.0,
            },
        }
        return params.get(regime, params[MarketRegime.RANGING])

    def should_trade(self, regime: MarketRegime, strategy_type: str) -> bool:
        regime_params = self.get_strategy_params(regime)
        weight = float(regime_params.get(f"{strategy_type}_weight", 0.0))
        return weight > 0.3

    def get_regime_duration(self) -> int:
        if not self.regime_history:
            return 0
        current = self.current_regime.value
        duration = 0
        for entry in reversed(self.regime_history):
            if entry.get("regime") == current:
                duration += 1
            else:
                break
        return duration
