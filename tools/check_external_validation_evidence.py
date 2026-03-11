#!/usr/bin/env python3
"""Validate external user-validation evidence metadata contract (COMP-18)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_FIELD_RE = {
    "release_window": re.compile(
        r"^\s*[-*]?\s*`?release_window\s*:\s*(.+?)`?\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    ),
    "external_beginner_participants": re.compile(
        r"^\s*[-*]?\s*`?external_beginner_participants\s*:\s*(\d+)`?\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    ),
    "external_pro_participants": re.compile(
        r"^\s*[-*]?\s*`?external_pro_participants\s*:\s*(\d+)`?\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    ),
    "internal_proxy_participants": re.compile(
        r"^\s*[-*]?\s*`?internal_proxy_participants\s*:\s*(\d+)`?\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    ),
}


def _extract_int(pattern: re.Pattern[str], text: str) -> int | None:
    match = pattern.search(text)
    if not match:
        return None
    return int(match.group(1))


def evaluate_external_validation(*, user_research_path: Path, readme_path: Path) -> list[str]:
    errors: list[str] = []
    research = user_research_path.read_text(encoding="utf-8")
    readme = readme_path.read_text(encoding="utf-8")

    release_window_match = _FIELD_RE["release_window"].search(research)
    if not release_window_match:
        errors.append("USER_RESEARCH: missing `release_window: YYYY-MM`")

    beginner = _extract_int(_FIELD_RE["external_beginner_participants"], research)
    pro = _extract_int(_FIELD_RE["external_pro_participants"], research)
    internal = _extract_int(_FIELD_RE["internal_proxy_participants"], research)

    if beginner is None:
        errors.append("USER_RESEARCH: missing `external_beginner_participants`")
    if pro is None:
        errors.append("USER_RESEARCH: missing `external_pro_participants`")
    if internal is None:
        errors.append("USER_RESEARCH: missing `internal_proxy_participants`")

    external_total = int((beginner or 0) + (pro or 0))
    claim_requires_external = bool(
        re.search(r"equally\s+friendly\s+to\s+noobs\s+and\s+pros", readme, flags=re.IGNORECASE)
    )
    if claim_requires_external and external_total <= 0:
        errors.append(
            "README claim about noob/pro friendliness requires at least one external participant in current cohort"
        )

    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-research", default="docs/USER_RESEARCH_2026_03.md")
    parser.add_argument("--readme", default="README.md")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors = evaluate_external_validation(
        user_research_path=Path(args.user_research),
        readme_path=Path(args.readme),
    )
    if errors:
        for item in errors:
            print(f"FAIL {item}")
        return 2
    print("PASS external validation evidence contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
