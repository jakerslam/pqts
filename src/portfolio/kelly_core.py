"""Shared Kelly sizing primitives used across strategy and portfolio modules."""

from __future__ import annotations


def clip_unit(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def implied_probability_from_payout(payout_multiple: float) -> float:
    """Convert payout multiple `b` (net odds) to implied probability 1/(1+b)."""
    b = float(payout_multiple)
    if b <= 0:
        raise ValueError("payout_multiple must be > 0.")
    return 1.0 / (1.0 + b)


def kelly_fraction_from_probability(*, posterior_probability: float, payout_multiple: float) -> float:
    """Kelly fraction using posterior win probability and payout multiple."""
    p = clip_unit(float(posterior_probability))
    q = 1.0 - p
    b = float(payout_multiple)
    if b <= 0:
        raise ValueError("payout_multiple must be > 0.")
    return (p * b - q) / b


def kelly_fraction_from_win_loss(*, win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Kelly fraction from win-rate and payoff ratio components."""
    p = clip_unit(float(win_rate))
    q = 1.0 - p
    avg_loss = max(float(avg_loss), 1e-12)
    b = max(float(avg_win) / avg_loss, 0.0)
    if b <= 0:
        return 0.0
    return (p * b - q) / b


def bounded_fraction(*, requested: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(max(float(requested), float(low)), float(high))
