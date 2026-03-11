#!/usr/bin/env python3
"""Run a ninety-day paper-trading harness using the monthly slice engine."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/paper.yaml")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--anchor-date", default="")
    parser.add_argument("--cycles-per-month", type=int, default=12)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--notional-usd", type=float, default=150.0)
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT,BTC-USD,ETH-USD")
    parser.add_argument("--risk-profile", default="balanced")
    parser.add_argument("--operator-tier", default="")
    parser.add_argument("--lookback-days", type=int, default=60)
    parser.add_argument("--min-days", type=int, default=1)
    parser.add_argument("--min-fills", type=int, default=10)
    parser.add_argument("--readiness-every", type=int, default=1)
    parser.add_argument("--max-p95-slippage-bps", type=float, default=25.0)
    parser.add_argument("--max-mape-pct", type=float, default=40.0)
    parser.add_argument("--max-reject-rate", type=float, default=1.0)
    parser.add_argument("--max-avg-reject-rate", type=float, default=0.5)
    parser.add_argument("--min-ready-months", type=int, default=1)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out-dir", default="data/reports/paper_90d")
    parser.add_argument("--tca-root", default="data/tca/paper_90d")
    return parser


def _months_for_days(days: int) -> int:
    if days <= 0:
        return 1
    # 90-day harness maps to three monthly slices by default.
    return max(1, int(round(float(days) / 30.0)))


def _parse_summary(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        token = line.strip()
        if not token:
            continue
        try:
            payload = json.loads(token)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def main() -> int:
    args = build_parser().parse_args()
    months = _months_for_days(int(args.days))
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_paper_6m_harness.py"),
        "--config",
        str(args.config),
        "--months",
        str(months),
        "--cycles-per-month",
        str(int(args.cycles_per_month)),
        "--sleep-seconds",
        str(float(args.sleep_seconds)),
        "--notional-usd",
        str(float(args.notional_usd)),
        "--symbols",
        str(args.symbols),
        "--risk-profile",
        str(args.risk_profile),
        "--lookback-days",
        str(int(args.lookback_days)),
        "--min-days",
        str(int(args.min_days)),
        "--min-fills",
        str(int(args.min_fills)),
        "--readiness-every",
        str(int(args.readiness_every)),
        "--max-p95-slippage-bps",
        str(float(args.max_p95_slippage_bps)),
        "--max-mape-pct",
        str(float(args.max_mape_pct)),
        "--max-reject-rate",
        str(float(args.max_reject_rate)),
        "--max-avg-reject-rate",
        str(float(args.max_avg_reject_rate)),
        "--min-ready-months",
        str(int(args.min_ready_months)),
        "--out-dir",
        str(args.out_dir),
        "--tca-root",
        str(args.tca_root),
    ]
    if str(args.anchor_date).strip():
        cmd.extend(["--anchor-date", str(args.anchor_date).strip()])
    if str(args.operator_tier).strip():
        cmd.extend(["--operator-tier", str(args.operator_tier).strip()])
    if bool(args.strict):
        cmd.append("--strict")

    completed = subprocess.run(  # noqa: S603
        cmd,
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)

    summary = _parse_summary(completed.stdout)
    if summary:
        summary["target_window_days"] = int(args.days)
        summary["months_executed"] = int(months)
        print(json.dumps(summary, sort_keys=True))
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
