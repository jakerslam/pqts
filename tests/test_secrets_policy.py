"""Tests for live secret policy enforcement."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.engine import TradingEngine
from core.secrets_policy import enforce_live_secrets, validate_live_secrets


def _live_config() -> dict:
    return {
        "mode": "live_trading",
        "markets": {
            "crypto": {
                "enabled": True,
                "exchanges": [
                    {
                        "name": "binance",
                        "api_key": "${BINANCE_API_KEY}",
                        "api_secret": "${BINANCE_API_SECRET}",
                        "symbols": ["BTCUSDT"],
                    }
                ],
            }
        },
        "strategies": {"trend_following": {"enabled": True, "markets": ["crypto"]}},
        "risk": {"initial_capital": 100000.0},
    }


def test_validate_live_secrets_flags_missing_env():
    issues = validate_live_secrets(_live_config(), env={})
    keys = {issue.key for issue in issues}
    assert "markets.crypto.exchanges[0].api_key" in keys
    assert "markets.crypto.exchanges[0].api_secret" in keys


def test_enforce_live_secrets_passes_when_env_present():
    env = {"BINANCE_API_KEY": "k_live", "BINANCE_API_SECRET": "s_live"}
    enforce_live_secrets(_live_config(), env=env)


def test_engine_rejects_live_config_without_required_secrets(tmp_path):
    config = _live_config()
    path = tmp_path / "live.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(RuntimeError):
        TradingEngine(str(path))


def test_engine_allows_placeholder_secrets_in_paper_mode(tmp_path):
    config = _live_config()
    config["mode"] = "paper_trading"
    path = tmp_path / "paper.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")

    engine = TradingEngine(str(path))
    assert engine.mode == "paper_trading"
