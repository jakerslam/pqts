#!/usr/bin/env python3
"""Validate that marketed paper-trading integrations have current certification evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_certified_integrations(
    *,
    integration_index_path: Path,
    certification_report_path: Path,
    required_venues: list[str],
    required_market_classes: list[str],
) -> list[str]:
    errors: list[str] = []

    raw_index = _load_json(integration_index_path)
    if not isinstance(raw_index, list):
        return [f"integration index must be a JSON array: {integration_index_path}"]
    entries = [row for row in raw_index if isinstance(row, dict)]

    by_provider: dict[str, dict] = {}
    covered_market_classes: set[str] = set()
    for row in entries:
        provider = str(row.get("provider", "")).strip().lower()
        if provider:
            by_provider[provider] = row
        for token in list(row.get("market_classes") or []):
            covered_market_classes.add(str(token).strip().lower())

    for required_market in required_market_classes:
        if required_market.lower() not in covered_market_classes:
            errors.append(
                f"integration index missing required market class '{required_market}'"
            )

    cert_raw = _load_json(certification_report_path)
    if not isinstance(cert_raw, dict):
        return [f"certification report must be a JSON object: {certification_report_path}"]
    if not bool(cert_raw.get("all_passed", False)):
        errors.append("certification report indicates failures (`all_passed=false`)")

    cert_results = cert_raw.get("results", [])
    if not isinstance(cert_results, list):
        cert_results = []
    cert_by_venue: dict[str, dict] = {}
    for row in cert_results:
        if not isinstance(row, dict):
            continue
        venue = str(row.get("venue", "")).strip().lower()
        if venue:
            cert_by_venue[venue] = row

    for venue in required_venues:
        venue_key = venue.strip().lower()
        if venue_key not in by_provider:
            errors.append(f"integration index missing provider '{venue_key}'")
            continue
        if venue_key not in cert_by_venue:
            errors.append(f"certification report missing venue '{venue_key}'")
            continue
        row = cert_by_venue[venue_key]
        if not bool(row.get("passed", False)):
            failures = list(row.get("failures") or [])
            errors.append(f"venue '{venue_key}' failed certification: {failures}")

    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default="config/integrations/official_integrations.json")
    parser.add_argument("--cert-report", default="data/reports/certifications/latest.json")
    parser.add_argument("--required-venues", default="binance,coinbase,alpaca,oanda")
    parser.add_argument("--required-market-classes", default="crypto,equities,forex,prediction_markets")
    return parser


def _csv(value: str) -> list[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def main() -> int:
    args = build_arg_parser().parse_args()
    errors = evaluate_certified_integrations(
        integration_index_path=Path(args.index),
        certification_report_path=Path(args.cert_report),
        required_venues=_csv(args.required_venues),
        required_market_classes=_csv(args.required_market_classes),
    )
    if errors:
        for item in errors:
            print(f"FAIL {item}")
        return 2
    print(
        json.dumps(
            {
                "validated": True,
                "index": args.index,
                "cert_report": args.cert_report,
                "required_venues": _csv(args.required_venues),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
