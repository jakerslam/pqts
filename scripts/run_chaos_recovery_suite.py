#!/usr/bin/env python3
"""Run deterministic chaos/recovery validation for reconnect, stale-feed, and kill-switch flows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DEFAULT_TEST_TARGETS = (
    "tests/test_live_ops_controls.py",
    "tests/test_market_data_resilience.py",
    "tests/test_ws_ingestion.py",
    "tests/test_kill_switches.py",
    "tests/test_reconciliation_daemon.py",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tests",
        default=",".join(DEFAULT_TEST_TARGETS),
        help="Comma-separated pytest target list.",
    )
    parser.add_argument("--out-dir", default="data/reports/chaos")
    parser.add_argument("--strict", action="store_true")
    return parser


def _csv(value: str) -> list[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def main() -> int:
    args = build_parser().parse_args()
    targets = _csv(args.tests)
    cmd = [sys.executable, "-m", "pytest", "-q", *targets]

    started = time.perf_counter()
    completed = subprocess.run(  # noqa: S603
        cmd,
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    duration_s = float(time.perf_counter() - started)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = out_dir / f"chaos_recovery_suite_{stamp}.json"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(cmd),
        "targets": targets,
        "duration_seconds": duration_s,
        "returncode": int(completed.returncode),
        "passed": completed.returncode == 0,
        "stdout_tail": completed.stdout.splitlines()[-40:],
        "stderr_tail": completed.stderr.splitlines()[-40:],
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report_path": str(report_path), "passed": report["passed"]}, sort_keys=True))

    if completed.returncode != 0:
        # Preserve full logs in CI console for quick diagnosis.
        if completed.stdout:
            print(completed.stdout)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)

    if args.strict:
        return int(completed.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
