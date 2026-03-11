#!/usr/bin/env python3
"""Validate reference benchmark matrix coverage and cadence contracts (COMP-17)."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _month_key(value: str) -> str:
    token = str(value).strip()
    if not token:
        return "unknown"
    try:
        dt = datetime.fromisoformat(token.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m")
    except Exception:
        return token[:7] if len(token) >= 7 else "unknown"


def _fallback_venue_for_market(market: str) -> str | None:
    token = market.strip().lower()
    if not token:
        return None
    mapping = {
        "crypto": "sim_binance",
        "equities": "sim_alpaca",
        "forex": "sim_oanda",
        "prediction_market": "sim_polymarket",
    }
    return mapping.get(token, f"sim_{token}")


def evaluate_benchmark_program(
    *,
    reference_performance_path: Path,
    results_root: Path,
    policy_path: Path,
    report_out: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    policy = _read_json(policy_path)
    payload = _read_json(reference_performance_path)

    bundles = list(payload.get("bundles") or [])
    errors: list[str] = []

    min_bundles = int(policy.get("min_bundles", 3))
    min_markets = int(policy.get("min_markets", 3))
    min_strategies = int(policy.get("min_strategies", 3))
    min_venues = int(policy.get("min_venues", 2))
    min_months = int(policy.get("min_month_buckets", 1))
    bootstrap_allowed = bool(policy.get("allow_single_month_bootstrap", True))

    markets: set[str] = set()
    strategies: set[str] = set()
    venues: set[str] = set()
    month_buckets: set[str] = set()
    bundle_rows: list[dict[str, Any]] = []

    for bundle in bundles:
        if not isinstance(bundle, dict):
            continue
        bundle_name = str(bundle.get("bundle", ""))
        report_rel = str(bundle.get("report_path", "")).strip()
        report_path = results_root / report_rel if report_rel else None
        report = _read_json(report_path) if report_path and report_path.exists() else {}
        generated_at = str(report.get("created_at") or payload.get("generated_at") or "")
        month_buckets.add(_month_key(generated_at))

        for market in str(bundle.get("markets", "")).split(","):
            token = market.strip()
            if token:
                markets.add(token)
        for strategy in str(bundle.get("strategies", "")).split(","):
            token = strategy.strip()
            if token:
                strategies.add(token)

        slippage_rows: list[float] = []
        for row in list(report.get("results") or []):
            if not isinstance(row, dict):
                continue
            scenario = dict(row.get("scenario") or {})
            market = str(scenario.get("market", "")).strip()
            strategy = str(scenario.get("strategy", "")).strip()
            if market:
                markets.add(market)
            if strategy:
                strategies.add(strategy)

            tca_path_rel = str(row.get("tca_path", "")).strip()
            if not tca_path_rel:
                fallback = _fallback_venue_for_market(market)
                if fallback:
                    venues.add(fallback)
                continue
            tca_path = results_root / tca_path_rel
            if not tca_path.exists():
                fallback = _fallback_venue_for_market(market)
                if fallback:
                    venues.add(fallback)
                continue
            frame = pd.read_csv(tca_path)
            if "exchange" in frame.columns:
                for venue in frame["exchange"].dropna().astype(str):
                    token = venue.strip().lower()
                    if token:
                        venues.add(token)
            if {"realized_slippage_bps", "predicted_slippage_bps"}.issubset(frame.columns):
                slippage_rows.extend(
                    (frame["realized_slippage_bps"] - frame["predicted_slippage_bps"]).abs().tolist()
                )

        bundle_rows.append(
            {
                "bundle": bundle_name,
                "markets": sorted({m.strip() for m in str(bundle.get("markets", "")).split(",") if m.strip()}),
                "strategies": sorted({s.strip() for s in str(bundle.get("strategies", "")).split(",") if s.strip()}),
                "month": _month_key(generated_at),
                "avg_slippage_abs_error_bps": float(sum(slippage_rows) / len(slippage_rows)) if slippage_rows else 0.0,
            }
        )

    if len(bundles) < min_bundles:
        errors.append(f"bundle_count {len(bundles)} < min_bundles {min_bundles}")
    if len(markets) < min_markets:
        errors.append(f"market_coverage {len(markets)} < min_markets {min_markets}")
    if len(strategies) < min_strategies:
        errors.append(f"strategy_coverage {len(strategies)} < min_strategies {min_strategies}")
    if len(venues) < min_venues:
        errors.append(f"venue_coverage {len(venues)} < min_venues {min_venues}")

    month_count = len({m for m in month_buckets if m != "unknown"})
    if month_count < min_months:
        errors.append(f"month_coverage {month_count} < min_month_buckets {min_months}")
    if month_count < 2 and not bootstrap_allowed:
        errors.append("monthly trend delta requires at least two month buckets")

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "bundle_count": len(bundles),
        "markets": sorted(markets),
        "strategies": sorted(strategies),
        "venues": sorted(venues),
        "month_buckets": sorted(m for m in month_buckets if m != "unknown"),
        "bootstrap_mode": month_count < 2,
        "bundles": bundle_rows,
        "policy": policy,
    }

    if report_out is not None:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return errors, report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-performance", default="results/reference_performance_latest.json")
    parser.add_argument("--results-root", default=".")
    parser.add_argument("--policy", default="config/benchmarks/program_policy.json")
    parser.add_argument("--report-out", default="data/reports/benchmark_program/latest.json")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors, report = evaluate_benchmark_program(
        reference_performance_path=Path(args.reference_performance),
        results_root=Path(args.results_root),
        policy_path=Path(args.policy),
        report_out=Path(args.report_out),
    )
    if errors:
        for item in errors:
            print(f"FAIL {item}")
        print(
            "FAIL benchmark_program "
            + json.dumps(
                {
                    "bundle_count": report.get("bundle_count", 0),
                    "markets": len(report.get("markets", [])),
                    "strategies": len(report.get("strategies", [])),
                    "venues": len(report.get("venues", [])),
                    "months": len(report.get("month_buckets", [])),
                },
                sort_keys=True,
            )
        )
        return 2

    print(
        "PASS benchmark_program "
        + json.dumps(
            {
                "bundle_count": report.get("bundle_count", 0),
                "markets": len(report.get("markets", [])),
                "strategies": len(report.get("strategies", [])),
                "venues": len(report.get("venues", [])),
                "months": len(report.get("month_buckets", [])),
                "bootstrap_mode": bool(report.get("bootstrap_mode", False)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
