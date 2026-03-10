import numpy as np
import pandas as pd

from strategies.regime_detector import MarketRegime, RegimeDetector


def test_regime_detector_compat_wrapper() -> None:
    rng = np.random.default_rng(7)
    close = 100.0 + np.cumsum(rng.normal(loc=0.05, scale=0.2, size=120))
    frame = pd.DataFrame(
        {
            "close": close,
            "high": close * 1.002,
            "low": close * 0.998,
            "volume": rng.integers(1_000, 5_000, size=120),
        },
        index=pd.date_range("2026-01-01", periods=120, freq="h"),
    )

    detector = RegimeDetector({})
    regime = detector.detect_regime(frame)
    assert isinstance(regime, MarketRegime)

    params = detector.get_strategy_params(regime)
    assert "position_size_multiplier" in params

    should_trade = detector.should_trade(regime, "trend_following")
    assert isinstance(should_trade, bool)
    assert detector.get_regime_duration() >= 1
