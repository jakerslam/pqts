from __future__ import annotations

import pytest

from research.analytics_data_plane import (
    classify_storage_tier,
    validate_local_data_format,
    validate_storage_tier_boundary,
)


def test_classify_storage_tier() -> None:
    assert classify_storage_tier("data/lake/ohlcv.parquet") == "local_analytics"
    assert classify_storage_tier("data/analytics/account.json") == "operational_state"
    assert classify_storage_tier("data/engine_state.json") == "operational_state"


def test_validate_storage_tier_boundary_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="storage tier mismatch"):
        validate_storage_tier_boundary(
            path="data/analytics/account.json",
            expected_tier="local_analytics",
        )


def test_validate_local_data_format_accepts_supported() -> None:
    assert validate_local_data_format("features.parquet")["validated"] is True
    with pytest.raises(ValueError, match="unsupported"):
        validate_local_data_format("features.sqlite")
