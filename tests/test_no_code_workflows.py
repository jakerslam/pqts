from __future__ import annotations

from app.no_code_workflows import NoCodeStrategySpec, build_no_code_manifest, kelly_disclosure, manifest_cli_equivalent


def test_no_code_manifest_and_cli_equivalent() -> None:
    spec = NoCodeStrategySpec(
        name="no_code_demo",
        market_scope="polymarket:crypto",
        direction_policy="yes",
        template="trend_following",
        params={"risk_profile": "conservative"},
    )
    manifest = build_no_code_manifest(spec)
    cli = manifest_cli_equivalent(manifest)
    assert "no_code_demo" in cli
    assert manifest["runtime_path"] == "execution.RiskAwareRouter.submit_order"


def test_kelly_disclosure_bounds() -> None:
    disclosure = kelly_disclosure(win_probability=0.6, payout_multiple=1.0, fees=0.01, fractional_cap=0.2)
    assert disclosure["kelly_fraction"] <= 0.2
