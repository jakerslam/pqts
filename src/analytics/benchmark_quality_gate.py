"""Benchmark quality gate classification for public reference reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class BenchmarkQualityThresholds:
    """Thresholds for classifying benchmark runs."""

    min_fill_rate: float = 0.000001
    max_reject_rate: float = 0.40
    min_scenarios: int = 1


@dataclass(frozen=True)
class BenchmarkQualityResult:
    """Outcome of benchmark quality evaluation."""

    passed: bool
    result_class: str
    include_in_reference_summary: bool
    avg_fill_rate_weighted: float
    avg_reject_rate_weighted: float
    scenarios_evaluated: int
    bundle_count: int
    checks: dict[str, bool]
    thresholds: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate_benchmark_quality(
    *,
    attribution_rows: Sequence[Mapping[str, object]],
    scenario_count: int,
    bundle_count: int,
    thresholds: BenchmarkQualityThresholds | None = None,
) -> BenchmarkQualityResult:
    """Classify benchmark quality for public reference use."""
    gate = thresholds or BenchmarkQualityThresholds()

    weighted_fill = 0.0
    weighted_reject = 0.0
    total_runs = 0
    non_zero_fill_rows = True
    reject_rate_rows = True

    for row in attribution_rows:
        runs = max(1, int(_safe_float(row.get("runs", 1), 1.0)))
        fill_rate = _safe_float(row.get("avg_fill_rate", 0.0))
        reject_rate = _safe_float(row.get("avg_reject_rate", 1.0), 1.0)
        total_runs += runs
        weighted_fill += fill_rate * runs
        weighted_reject += reject_rate * runs
        if fill_rate <= float(gate.min_fill_rate):
            non_zero_fill_rows = False
        if reject_rate > float(gate.max_reject_rate):
            reject_rate_rows = False

    avg_fill = (weighted_fill / total_runs) if total_runs else 0.0
    avg_reject = (weighted_reject / total_runs) if total_runs else 1.0

    has_scenarios = int(scenario_count) >= int(gate.min_scenarios)
    has_bundles = int(bundle_count) > 0
    checks = {
        "has_scenarios": bool(has_scenarios),
        "has_bundles": bool(has_bundles),
        "non_zero_fill_rows": bool(non_zero_fill_rows and total_runs > 0),
        "reject_rate_rows_within_limit": bool(reject_rate_rows and total_runs > 0),
    }
    passed = all(checks.values())
    result_class = "reference" if passed else "diagnostic_only"
    return BenchmarkQualityResult(
        passed=bool(passed),
        result_class=result_class,
        include_in_reference_summary=bool(passed),
        avg_fill_rate_weighted=float(avg_fill),
        avg_reject_rate_weighted=float(avg_reject),
        scenarios_evaluated=int(scenario_count),
        bundle_count=int(bundle_count),
        checks=checks,
        thresholds={
            "min_fill_rate": float(gate.min_fill_rate),
            "max_reject_rate": float(gate.max_reject_rate),
            "min_scenarios": float(gate.min_scenarios),
        },
    )
