from __future__ import annotations

from srs.assimilation_registry import ensure_srs_assimilation_coverage


def test_srs_assimilation_registry_covers_all_requirements() -> None:
    report = ensure_srs_assimilation_coverage()
    assert report["total_requirements"] >= 497
    assert report["registry_rows"] == report["total_requirements"]
    assert report["missing"] == []
    assert report["extra"] == []


def test_srs_assimilation_registry_includes_both_tiers() -> None:
    report = ensure_srs_assimilation_coverage()
    tier_counts = report["summary"]["tier_counts"]
    assert tier_counts.get("core_delivery", 0) > 0
    assert tier_counts.get("baseline_contract", 0) >= 0
    assert (
        tier_counts.get("core_delivery", 0)
        + tier_counts.get("baseline_contract", 0)
        == report["registry_rows"]
    )
