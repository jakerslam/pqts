#!/usr/bin/env python3
"""Validate freshness of competitor source references."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
import sys

from python_bootstrap import ensure_repo_python_path

REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path = [REPO_ROOT, *sys.path]
ensure_repo_python_path()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="config/moat/competitor_sources.json")
    parser.add_argument("--max-age-days", type=int, default=30)
    parser.add_argument("--today", default="")
    return parser


def main() -> int:
    from moat.competitor_revalidation import CompetitorSource, evaluate_source_freshness

    args = build_arg_parser().parse_args()
    payload = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    rows = [CompetitorSource(**item) for item in payload.get("sources", [])]
    today = date.fromisoformat(args.today) if args.today else date.today()

    report = evaluate_source_freshness(
        sources=rows,
        today=today,
        max_age_days=int(args.max_age_days),
    )
    if not report["passed"]:
        raise SystemExit(json.dumps(report, sort_keys=True))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
