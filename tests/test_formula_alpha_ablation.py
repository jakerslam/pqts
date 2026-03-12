from analytics.formula_alpha_ablation import evaluate_formula_alpha_ablation


def test_formula_alpha_ablation_passes_with_consistent_positive_lift() -> None:
    model = [4.0, 3.5, 5.0, 4.2, 3.8] * 8
    baseline = [1.5, 1.0, 2.1, 1.9, 1.3] * 8
    result = evaluate_formula_alpha_ablation(
        model_net_alpha_bps=model,
        baseline_net_alpha_bps=baseline,
        min_samples=30,
        min_lift_bps=1.0,
        min_positive_lift_rate=0.6,
    )
    assert result.passed is True
    assert result.lift_mean_bps >= 1.0
    assert result.positive_lift_rate >= 0.6


def test_formula_alpha_ablation_fails_when_lift_is_not_supported() -> None:
    model = [1.0, 1.1, 0.9, 1.0] * 10
    baseline = [1.0, 1.2, 1.0, 1.1] * 10
    result = evaluate_formula_alpha_ablation(
        model_net_alpha_bps=model,
        baseline_net_alpha_bps=baseline,
        min_samples=30,
        min_lift_bps=0.5,
        min_positive_lift_rate=0.6,
    )
    assert result.passed is False
    assert "lift_below_threshold" in result.reason_codes
