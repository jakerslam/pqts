from __future__ import annotations

from analytics.benchmark_quality_gate import BenchmarkQualityThresholds, evaluate_benchmark_quality


def test_quality_gate_passes_reference_when_fill_non_zero_and_reject_low() -> None:
    result = evaluate_benchmark_quality(
        attribution_rows=[
            {
                "market": "crypto",
                "strategy": "market_making",
                "runs": 3,
                "avg_fill_rate": 0.42,
                "avg_reject_rate": 0.18,
            }
        ],
        scenario_count=3,
        bundle_count=1,
    )

    assert result.passed is True
    assert result.result_class == "reference"
    assert result.include_in_reference_summary is True


def test_quality_gate_marks_diagnostic_when_any_check_fails() -> None:
    result = evaluate_benchmark_quality(
        attribution_rows=[
            {
                "market": "crypto",
                "strategy": "market_making",
                "runs": 2,
                "avg_fill_rate": 0.0,
                "avg_reject_rate": 0.75,
            }
        ],
        scenario_count=2,
        bundle_count=1,
        thresholds=BenchmarkQualityThresholds(min_fill_rate=0.000001, max_reject_rate=0.4),
    )

    assert result.passed is False
    assert result.result_class == "diagnostic_only"
    assert result.include_in_reference_summary is False
    assert result.checks["non_zero_fill_rows"] is False
    assert result.checks["reject_rate_rows_within_limit"] is False
