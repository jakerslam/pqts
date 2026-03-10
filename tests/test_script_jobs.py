from __future__ import annotations

from pathlib import Path

from app.script_jobs import build_paper_campaign_job, build_simulation_suite_job


def test_build_simulation_suite_job_includes_required_args() -> None:
    job = build_simulation_suite_job(
        repo_root=Path("/repo"),
        config="config/paper.yaml",
        markets="crypto",
        strategies="trend_following",
        cycles=6,
        readiness_every=3,
        symbols_per_market=1,
        out_dir="data/reports/demo",
        telemetry_log="data/analytics/simulation_events.jsonl",
        tca_dir="data/tca/simulation",
        risk_profile="balanced",
    )
    command = job.command("/usr/bin/python3")
    joined = " ".join(command)
    assert command[0] == "/usr/bin/python3"
    assert "run_simulation_suite.py" in joined
    assert "--markets crypto" in joined
    assert "--strategies trend_following" in joined
    assert "--risk-profile balanced" in joined


def test_build_paper_campaign_job_omits_optional_flags_when_empty() -> None:
    job = build_paper_campaign_job(
        repo_root=Path("/repo"),
        config="config/paper.yaml",
        cycles=8,
        sleep_seconds=0.0,
        notional_usd=125.0,
        readiness_every=5,
        out_dir="data/reports/paper",
        symbols="",
        risk_profile="",
    )
    command = job.command("python")
    assert "run_paper_campaign.py" in " ".join(command)
    assert "--symbols" not in command
    assert "--risk-profile" not in command

