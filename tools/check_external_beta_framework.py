#!/usr/bin/env python3
"""Validate external beta cohort registry contract and monthly alignment."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


_RELEASE_RE = re.compile(r"^\d{4}-\d{2}$")
_ALLOWED_STATUS = {"planned", "active", "completed"}


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_release_window(user_research_path: Path) -> str:
    text = user_research_path.read_text(encoding="utf-8")
    match = re.search(
        r"^\s*[-*]?\s*`?release_window\s*:\s*([0-9]{4}-[0-9]{2})`?\s*$",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return str(match.group(1)).strip() if match else ""


def evaluate_external_beta_framework(*, registry_path: Path, user_research_path: Path) -> list[str]:
    errors: list[str] = []
    payload = _load_json(registry_path)
    if not isinstance(payload, dict):
        return [f"registry must be a JSON object: {registry_path}"]

    schema_version = str(payload.get("schema_version", "")).strip()
    if not schema_version:
        errors.append("registry missing schema_version")

    cohorts = payload.get("cohorts", [])
    if not isinstance(cohorts, list) or not cohorts:
        errors.append("registry requires at least one cohort entry")
        return errors

    current_release_window = _extract_release_window(user_research_path)
    if not current_release_window:
        errors.append("user research document missing release_window metadata")

    windows: set[str] = set()
    has_current_window = False
    for idx, row in enumerate(cohorts, start=1):
        if not isinstance(row, dict):
            errors.append(f"cohorts[{idx}] must be object")
            continue
        window = str(row.get("release_window", "")).strip()
        status = str(row.get("status", "")).strip().lower()
        if not _RELEASE_RE.match(window):
            errors.append(f"cohorts[{idx}] invalid release_window '{window}'")
        elif window in windows:
            errors.append(f"cohorts[{idx}] duplicate release_window '{window}'")
        else:
            windows.add(window)
        if status not in _ALLOWED_STATUS:
            errors.append(f"cohorts[{idx}] invalid status '{status}'")
        for key in (
            "external_beginner_participants",
            "external_pro_participants",
            "internal_proxy_participants",
        ):
            value = row.get(key)
            if not isinstance(value, int) or value < 0:
                errors.append(f"cohorts[{idx}] {key} must be a non-negative integer")
        channels = row.get("channels", [])
        if not isinstance(channels, list) or not channels:
            errors.append(f"cohorts[{idx}] channels must be a non-empty list")
        if window and window == current_release_window:
            has_current_window = True

    if current_release_window and not has_current_window:
        errors.append(
            f"registry missing cohort entry for current release_window '{current_release_window}'"
        )
    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="data/validation/external_beta/cohort_registry.json")
    parser.add_argument("--user-research", default="docs/USER_RESEARCH_2026_03.md")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors = evaluate_external_beta_framework(
        registry_path=Path(args.registry),
        user_research_path=Path(args.user_research),
    )
    if errors:
        for item in errors:
            print(f"FAIL {item}")
        return 2
    print(
        json.dumps(
            {
                "validated": True,
                "registry": args.registry,
                "user_research": args.user_research,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
