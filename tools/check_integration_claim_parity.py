#!/usr/bin/env python3
"""Validate README integration/market claims against canonical integration index (PMKT-16)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_market_classes(rows: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for row in rows:
        market_classes = row.get("market_classes")
        if isinstance(market_classes, list):
            for token in market_classes:
                value = str(token).strip().lower()
                if value:
                    out.add(value)
    return out


def _collect_provider_aliases(rows: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for row in rows:
        provider = str(row.get("provider", "")).strip().lower()
        if provider:
            out.add(provider)
        aliases = row.get("aliases")
        if isinstance(aliases, list):
            for token in aliases:
                value = str(token).strip().lower()
                if value:
                    out.add(value)
    return out


def evaluate_claim_parity(*, readme_path: Path, index_path: Path) -> list[str]:
    errors: list[str] = []
    readme = readme_path.read_text(encoding="utf-8")
    raw = _read_json(index_path)
    if not isinstance(raw, list):
        raise ValueError("integration index must be a list")
    rows = [dict(row) for row in raw if isinstance(row, dict)]

    market_classes = _collect_market_classes(rows)
    provider_aliases = _collect_provider_aliases(rows)

    if re.search(r"crypto,\s*equities,\s*and\s*forex", readme, flags=re.IGNORECASE):
        required = {"crypto", "equities", "forex"}
        missing = sorted(required - market_classes)
        if missing:
            errors.append(
                f"README claims crypto/equities/forex but integration index missing market_classes: {missing}"
            )

    venues_match = re.search(r"--venues\s+([a-zA-Z0-9_,-]+)", readme)
    if venues_match:
        claimed = {
            token.strip().lower()
            for token in venues_match.group(1).split(",")
            if token.strip()
        }
        missing_venues = sorted(claimed - provider_aliases)
        if missing_venues:
            errors.append(
                "README certification venue list has no matching integration aliases: "
                + ", ".join(missing_venues)
            )

    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", default="README.md")
    parser.add_argument("--index", default="config/integrations/official_integrations.json")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors = evaluate_claim_parity(readme_path=Path(args.readme), index_path=Path(args.index))
    if errors:
        for item in errors:
            print(f"FAIL {item}")
        return 2
    print("PASS integration claim parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
