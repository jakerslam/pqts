from portfolio.kelly_core import (
    bounded_fraction,
    clip_unit,
    implied_probability_from_payout,
    kelly_fraction_from_probability,
    kelly_fraction_from_win_loss,
)


def test_clip_and_bounds() -> None:
    assert clip_unit(-1.0) == 0.0
    assert clip_unit(0.5) == 0.5
    assert clip_unit(2.0) == 1.0
    assert bounded_fraction(requested=1.5, low=0.0, high=1.0) == 1.0


def test_implied_probability_from_payout() -> None:
    assert abs(implied_probability_from_payout(1.0) - 0.5) < 1e-12


def test_kelly_probability_form() -> None:
    fraction = kelly_fraction_from_probability(
        posterior_probability=0.6,
        payout_multiple=1.0,
    )
    assert abs(fraction - 0.2) < 1e-12


def test_kelly_win_loss_form() -> None:
    fraction = kelly_fraction_from_win_loss(
        win_rate=0.55,
        avg_win=0.02,
        avg_loss=0.01,
    )
    assert fraction > 0.0
