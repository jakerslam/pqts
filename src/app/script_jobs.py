"""Shared script-job builders for first-success CLI orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScriptJob:
    """Executable Python script invocation with stable cwd/args contract."""

    script_path: Path
    args: tuple[str, ...]
    cwd: Path

    def command(self, python_executable: str) -> list[str]:
        return [str(python_executable), str(self.script_path), *list(self.args)]


def build_simulation_suite_job(
    *,
    repo_root: Path,
    config: str,
    markets: str,
    strategies: str,
    cycles: int,
    readiness_every: int,
    symbols_per_market: int,
    out_dir: str,
    telemetry_log: str,
    tca_dir: str,
    risk_profile: str = "",
) -> ScriptJob:
    args: list[str] = [
        "--config",
        str(config),
        "--markets",
        str(markets),
        "--strategies",
        str(strategies),
        "--cycles-per-scenario",
        str(int(cycles)),
        "--readiness-every",
        str(int(readiness_every)),
        "--symbols-per-market",
        str(int(symbols_per_market)),
        "--sleep-seconds",
        "0.0",
        "--out-dir",
        str(out_dir),
        "--telemetry-log",
        str(telemetry_log),
        "--tca-dir",
        str(tca_dir),
    ]
    risk_token = str(risk_profile).strip()
    if risk_token:
        args.extend(["--risk-profile", risk_token])
    return ScriptJob(
        script_path=repo_root / "scripts" / "run_simulation_suite.py",
        args=tuple(args),
        cwd=repo_root,
    )


def build_paper_campaign_job(
    *,
    repo_root: Path,
    config: str,
    cycles: int,
    sleep_seconds: float,
    notional_usd: float,
    readiness_every: int,
    out_dir: str,
    symbols: str = "",
    risk_profile: str = "",
) -> ScriptJob:
    args: list[str] = [
        "--config",
        str(config),
        "--cycles",
        str(int(cycles)),
        "--sleep-seconds",
        str(float(sleep_seconds)),
        "--notional-usd",
        str(float(notional_usd)),
        "--readiness-every",
        str(int(readiness_every)),
        "--out-dir",
        str(out_dir),
    ]
    symbol_token = str(symbols).strip()
    if symbol_token:
        args.extend(["--symbols", symbol_token])
    risk_token = str(risk_profile).strip()
    if risk_token:
        args.extend(["--risk-profile", risk_token])
    return ScriptJob(
        script_path=repo_root / "scripts" / "run_paper_campaign.py",
        args=tuple(args),
        cwd=repo_root,
    )

