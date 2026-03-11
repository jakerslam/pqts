from __future__ import annotations

import json
from pathlib import Path

from tools.check_certified_paper_integrations import evaluate_certified_integrations


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_certified_integrations_pass_for_required_venues(tmp_path: Path) -> None:
    index = _write(
        tmp_path / "integrations.json",
        [
            {"provider": "Binance", "market_classes": ["crypto"]},
            {"provider": "Coinbase", "market_classes": ["crypto"]},
            {"provider": "Alpaca", "market_classes": ["equities"]},
            {"provider": "Oanda", "market_classes": ["forex"]},
            {"provider": "Polymarket", "market_classes": ["prediction_markets"]},
        ],
    )
    cert = _write(
        tmp_path / "cert.json",
        {
            "all_passed": True,
            "results": [
                {"venue": "binance", "passed": True},
                {"venue": "coinbase", "passed": True},
                {"venue": "alpaca", "passed": True},
                {"venue": "oanda", "passed": True},
            ],
        },
    )
    errors = evaluate_certified_integrations(
        integration_index_path=index,
        certification_report_path=cert,
        required_venues=["binance", "coinbase", "alpaca", "oanda"],
        required_market_classes=["crypto", "equities", "forex", "prediction_markets"],
    )
    assert errors == []


def test_certified_integrations_flags_missing_or_failed_venues(tmp_path: Path) -> None:
    index = _write(
        tmp_path / "integrations.json",
        [
            {"provider": "Binance", "market_classes": ["crypto"]},
            {"provider": "Coinbase", "market_classes": ["crypto"]},
        ],
    )
    cert = _write(
        tmp_path / "cert.json",
        {
            "all_passed": False,
            "results": [
                {"venue": "binance", "passed": False, "failures": ["submit_order_check_failed"]},
            ],
        },
    )
    errors = evaluate_certified_integrations(
        integration_index_path=index,
        certification_report_path=cert,
        required_venues=["binance", "coinbase", "alpaca", "oanda"],
        required_market_classes=["crypto", "equities", "forex"],
    )
    assert any("all_passed=false" in item for item in errors)
    assert any("failed certification" in item for item in errors)
    assert any("missing provider 'alpaca'" in item for item in errors)
