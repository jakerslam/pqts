#!/usr/bin/env python3
"""Environment-driven deployment entrypoint with explicit run-mode contracts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if SRC.exists():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path[:] = [src_str, *sys.path]
if str(ROOT) not in sys.path:
    sys.path[:] = [str(ROOT), *sys.path]

from app.run_mode_contract import SUPPORTED_RUN_MODES, build_run_mode_plan  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-plan", action="store_true", help="Print resolved plan and exit.")
    parser.add_argument("--json", action="store_true", help="Print plan as JSON.")
    parser.add_argument(
        "--allow-missing-env",
        action="store_true",
        help="Bypass required env checks for diagnostics.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    plan = build_run_mode_plan()
    payload = {
        "mode": plan.mode,
        "command": list(plan.command),
        "required_env": list(plan.required_env),
        "missing_env": list(plan.missing_env),
        "supported_modes": sorted(SUPPORTED_RUN_MODES),
    }
    if args.print_plan or args.json:
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"Mode: {plan.mode}")
            print(f"Command: {' '.join(plan.command)}")
            if plan.required_env:
                print(f"Required env: {', '.join(plan.required_env)}")
            if plan.missing_env:
                print(f"Missing env: {', '.join(plan.missing_env)}")
        if args.print_plan:
            return 0

    if (not args.allow_missing_env) and plan.missing_env:
        print(
            f"Run mode '{plan.mode}' blocked: missing required env vars: "
            + ", ".join(plan.missing_env),
            file=sys.stderr,
        )
        return 2

    completed = subprocess.run(plan.command, cwd=str(ROOT), check=False)  # noqa: S603
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
