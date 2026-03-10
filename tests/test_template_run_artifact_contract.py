from __future__ import annotations

from contracts.template_run_artifact import TemplateRunArtifact


def test_template_run_artifact_to_dict_merges_extra_fields() -> None:
    artifact = TemplateRunArtifact(
        mode="backtest",
        template="momentum",
        resolved_strategy="trend_following",
        config_path="config/paper.yaml",
        config_sha256="abc123",
        command=("python", "scripts/run_simulation_suite.py"),
        extra={"market": "crypto", "cycles": 12},
    )
    payload = artifact.to_dict()
    assert payload["mode"] == "backtest"
    assert payload["template"] == "momentum"
    assert payload["resolved_strategy"] == "trend_following"
    assert payload["command"] == ["python", "scripts/run_simulation_suite.py"]
    assert payload["market"] == "crypto"
    assert payload["cycles"] == 12
    assert "generated_at" in payload

