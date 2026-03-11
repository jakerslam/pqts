from __future__ import annotations

import json
from pathlib import Path

from tools.check_integration_claim_parity import evaluate_claim_parity


def test_integration_claim_parity_passes_when_markets_and_aliases_match(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "Platform for crypto, equities, and forex markets.\n"
        "python scripts/run_exchange_certification.py --venues binance,coinbase,alpaca,oanda\n",
        encoding="utf-8",
    )
    index = tmp_path / "index.json"
    index.write_text(
        json.dumps(
            [
                {"provider": "Binance", "aliases": ["binance"], "market_classes": ["crypto"]},
                {"provider": "Coinbase", "aliases": ["coinbase"], "market_classes": ["crypto"]},
                {"provider": "Alpaca", "aliases": ["alpaca"], "market_classes": ["equities"]},
                {"provider": "Oanda", "aliases": ["oanda"], "market_classes": ["forex"]},
            ]
        ),
        encoding="utf-8",
    )
    assert evaluate_claim_parity(readme_path=readme, index_path=index) == []


def test_integration_claim_parity_flags_missing_market_class(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("Platform for crypto, equities, and forex markets.\n", encoding="utf-8")
    index = tmp_path / "index.json"
    index.write_text(
        json.dumps([{"provider": "Binance", "aliases": ["binance"], "market_classes": ["crypto"]}]),
        encoding="utf-8",
    )
    errors = evaluate_claim_parity(readme_path=readme, index_path=index)
    assert any("missing market_classes" in item for item in errors)
