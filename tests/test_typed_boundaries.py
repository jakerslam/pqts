from __future__ import annotations

import pytest
from pydantic import ValidationError

from contracts.typed_boundaries import APIPayloadModel, RuntimeConfigModel, StrategyManifestModel


def test_strategy_manifest_model_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        StrategyManifestModel(
            name="market_making",
            market="crypto",
            risk_profile="balanced",
            notional_usd=100.0,
            extra_field="x",
        )


def test_runtime_config_model_validates_positive_slos() -> None:
    model = RuntimeConfigModel(
        mode="paper_trading",
        ui_primary="dash",
        control_plane_base_url="http://localhost:8000",
        cycle_slo_ms=1000,
        refresh_slo_ms=5000,
    )
    assert model.mode == "paper_trading"


def test_api_payload_requires_non_empty_fields() -> None:
    with pytest.raises(ValidationError):
        APIPayloadModel(action="", account_id="a", strategy="b", run_id="c")
