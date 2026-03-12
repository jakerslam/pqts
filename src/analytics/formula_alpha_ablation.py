"""Formula-only alpha ablation checks for promotion blocking policies."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any, Sequence


@dataclass(frozen=True)
class FormulaAblationResult:
    passed: bool
    sample_count: int
    model_mean_bps: float
    baseline_mean_bps: float
    lift_mean_bps: float
    positive_lift_rate: float
    t_statistic: float
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_formula_alpha_ablation(
    *,
    model_net_alpha_bps: Sequence[float],
    baseline_net_alpha_bps: Sequence[float],
    min_samples: int = 30,
    min_lift_bps: float = 0.5,
    min_positive_lift_rate: float = 0.55,
) -> FormulaAblationResult:
    model = [float(x) for x in model_net_alpha_bps]
    baseline = [float(x) for x in baseline_net_alpha_bps]
    if len(model) != len(baseline):
        raise ValueError("model_net_alpha_bps and baseline_net_alpha_bps length mismatch.")

    n = len(model)
    reason_codes: list[str] = []
    if n < int(min_samples):
        reason_codes.append("insufficient_samples")

    model_mean = sum(model) / n if n else 0.0
    baseline_mean = sum(baseline) / n if n else 0.0
    lifts = [m - b for m, b in zip(model, baseline)]
    lift_mean = sum(lifts) / n if n else 0.0
    positive_lift_rate = (sum(1 for x in lifts if x > 0.0) / n) if n else 0.0
    if lift_mean < float(min_lift_bps):
        reason_codes.append("lift_below_threshold")
    if positive_lift_rate < float(min_positive_lift_rate):
        reason_codes.append("positive_lift_rate_below_threshold")

    if n > 1:
        variance = sum((x - lift_mean) ** 2 for x in lifts) / (n - 1)
        std = sqrt(max(variance, 0.0))
        t_stat = (lift_mean / (std / sqrt(n))) if std > 0.0 else (999.0 if lift_mean > 0.0 else 0.0)
    else:
        t_stat = 0.0

    return FormulaAblationResult(
        passed=not reason_codes,
        sample_count=n,
        model_mean_bps=float(model_mean),
        baseline_mean_bps=float(baseline_mean),
        lift_mean_bps=float(lift_mean),
        positive_lift_rate=float(positive_lift_rate),
        t_statistic=float(t_stat),
        reason_codes=tuple(reason_codes),
    )
