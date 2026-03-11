#!/usr/bin/env python3
"""Validate default policy coverage for SRS sections 66-71."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED = {
    "GIPP": [f"GIPP-{i}" for i in range(1, 9)],
    "MARIK": [f"MARIK-{i}" for i in range(1, 9)],
    "DUNIK": [f"DUNIK-{i}" for i in range(1, 9)],
    "ZERQ": [f"ZERQ-{i}" for i in range(1, 9)],
    "ANTP": [f"ANTP-{i}" for i in range(1, 9)],
    "MTM": [f"MTM-{i}" for i in range(1, 13)],
}


def evaluate_defaults(config_path: Path) -> list[str]:
    errors: list[str] = []
    if not config_path.exists():
        return [f"missing config file: {config_path}"]

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    families = payload.get("families")
    if not isinstance(families, dict):
        return ["config missing 'families' object"]

    for family, expected_refs in EXPECTED.items():
        block = families.get(family)
        if not isinstance(block, dict):
            errors.append(f"missing family block: {family}")
            continue
        refs = block.get("refs")
        controls = block.get("controls")
        evidence = block.get("acceptance_evidence")
        if refs != expected_refs:
            errors.append(f"{family} refs mismatch; expected {expected_refs}, got {refs}")
        if not isinstance(controls, dict) or not controls:
            errors.append(f"{family} controls missing or empty")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{family} acceptance_evidence missing or empty")
    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/strategy/assimilation_66_71_defaults.json")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors = evaluate_defaults(Path(args.config))
    payload = {"ok": not errors, "error_count": len(errors), "errors": errors}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

