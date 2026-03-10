#!/usr/bin/env python3
"""Update the canonical benchmark provenance JSONL log for a target month."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
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

from analytics.benchmark_provenance import update_monthly_benchmark_provenance_log  # noqa: E402


def _default_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--month", default=_default_month(), help="Target month in YYYY-MM format")
    parser.add_argument("--out", default="data/reports/provenance/benchmark_provenance.jsonl")
    parser.add_argument("--dataset-version", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    log_path = update_monthly_benchmark_provenance_log(
        results_dir=str(args.results_dir),
        month=str(args.month),
        output_path=str(args.out),
        repo_root=str(ROOT),
        dataset_version=args.dataset_version,
    )
    print(json.dumps({"provenance_log_path": str(log_path), "month": str(args.month)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
