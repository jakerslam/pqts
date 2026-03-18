"""Positive-skew strategy diagnostics and loss-cluster governance."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Any


@dataclass(frozen=True)
class SkewTradeObservation:
    trade_id: str
    pnl: float


@dataclass(frozen=True)
class PositiveSkewMetrics:
    expectancy: float
    payoff_ratio: float
    hit_rate: float
    median_loss: float
    tail_win_contribution: float
    top_win_pnl_concentration: float
    unrealistic_tail_dependency: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "expectancy": float(self.expectancy),
            "payoff_ratio": float(self.payoff_ratio),
            "hit_rate": float(self.hit_rate),
            "median_loss": float(self.median_loss),
            "tail_win_contribution": float(self.tail_win_contribution),
            "top_win_pnl_concentration": float(self.top_win_pnl_concentration),
            "unrealistic_tail_dependency": bool(self.unrealistic_tail_dependency),
        }


@dataclass(frozen=True)
class LossClusterDecision:
    action: str
    observed_loss_streak: int
    drawdown_pct: float
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "observed_loss_streak": int(self.observed_loss_streak),
            "drawdown_pct": float(self.drawdown_pct),
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class HitRateIllusionCheck:
    pass_check: bool
    reason_codes: tuple[str, ...]
    observed_hit_rate: float
    observed_payoff_ratio: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "pass_check": bool(self.pass_check),
            "reason_codes": list(self.reason_codes),
            "observed_hit_rate": float(self.observed_hit_rate),
            "observed_payoff_ratio": float(self.observed_payoff_ratio),
        }


def evaluate_positive_skew_basket_expectancy(
    trades: list[SkewTradeObservation],
    *,
    top_tail_n: int = 3,
    max_top_win_concentration: float = 0.75,
    min_tail_win_contribution: float = 0.15,
) -> PositiveSkewMetrics:
    """Compute skew-aware performance metrics and tail-dependency flag."""

    if not trades:
        raise ValueError("at least one trade observation is required")
    pnls = [float(row.pnl) for row in trades]
    wins = [x for x in pnls if x > 0.0]
    losses = [x for x in pnls if x < 0.0]
    if not wins or not losses:
        raise ValueError("skew metrics require both wins and losses")

    expectancy = float(mean(pnls))
    avg_win = float(mean(wins))
    avg_loss_abs = abs(float(mean(losses)))
    payoff_ratio = avg_win / max(avg_loss_abs, 1e-9)
    hit_rate = float(len(wins)) / float(len(pnls))
    median_loss = float(median(losses))
    tail_wins = sorted(wins, reverse=True)[: max(int(top_tail_n), 1)]
    total_positive = sum(wins)
    total_net = sum(pnls)
    top_win_pnl_concentration = sum(tail_wins) / max(total_positive, 1e-9)
    tail_win_contribution = sum(tail_wins) / max(total_net, 1e-9)
    unrealistic_tail_dependency = bool(
        top_win_pnl_concentration > float(max_top_win_concentration)
        or tail_win_contribution < float(min_tail_win_contribution)
    )
    return PositiveSkewMetrics(
        expectancy=expectancy,
        payoff_ratio=payoff_ratio,
        hit_rate=hit_rate,
        median_loss=median_loss,
        tail_win_contribution=tail_win_contribution,
        top_win_pnl_concentration=top_win_pnl_concentration,
        unrealistic_tail_dependency=unrealistic_tail_dependency,
    )


def evaluate_loss_cluster_tolerance(
    *,
    outcomes: list[float],
    max_consecutive_losses: int,
    max_drawdown_pct: float,
) -> LossClusterDecision:
    """Reduce or halt when loss clustering exceeds modeled tolerance."""

    if not outcomes:
        raise ValueError("outcomes are required")
    if int(max_consecutive_losses) <= 0:
        raise ValueError("max_consecutive_losses must be > 0")
    if float(max_drawdown_pct) <= 0.0:
        raise ValueError("max_drawdown_pct must be > 0")

    current_streak = 0
    worst_streak = 0
    equity = 0.0
    peak = 0.0
    worst_drawdown = 0.0
    for pnl in outcomes:
        value = float(pnl)
        if value < 0.0:
            current_streak += 1
            worst_streak = max(worst_streak, current_streak)
        else:
            current_streak = 0
        equity += value
        peak = max(peak, equity)
        drawdown = (peak - equity) / max(abs(peak), 1.0)
        worst_drawdown = max(worst_drawdown, drawdown)

    reasons: list[str] = []
    action = "allow"
    if worst_streak > int(max_consecutive_losses):
        reasons.append("loss_cluster_tolerance_breached")
        action = "reduce"
    if worst_drawdown > float(max_drawdown_pct):
        reasons.append("drawdown_envelope_breached")
        action = "halt"
    return LossClusterDecision(
        action=action,
        observed_loss_streak=worst_streak,
        drawdown_pct=worst_drawdown,
        reason_codes=tuple(sorted(set(reasons))),
    )


def falsify_hit_rate_illusion(
    *,
    observed_hit_rate: float,
    observed_payoff_ratio: float,
    expected_hit_rate_band: tuple[float, float],
    expected_payoff_ratio_band: tuple[float, float],
) -> HitRateIllusionCheck:
    """Validate observed results against declared skew payout assumptions."""

    hit = float(observed_hit_rate)
    payoff = float(observed_payoff_ratio)
    hit_low, hit_high = (float(expected_hit_rate_band[0]), float(expected_hit_rate_band[1]))
    pr_low, pr_high = (
        float(expected_payoff_ratio_band[0]),
        float(expected_payoff_ratio_band[1]),
    )
    reasons: list[str] = []
    if hit < hit_low or hit > hit_high:
        reasons.append("hit_rate_outside_declared_skew_band")
    if payoff < pr_low or payoff > pr_high:
        reasons.append("payoff_ratio_outside_declared_skew_band")
    return HitRateIllusionCheck(
        pass_check=not bool(reasons),
        reason_codes=tuple(sorted(set(reasons))),
        observed_hit_rate=hit,
        observed_payoff_ratio=payoff,
    )
