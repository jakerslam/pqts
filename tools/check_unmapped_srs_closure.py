#!/usr/bin/env python3
"""Verify closure mapping for previously unmapped P2 SRS families."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXPECTED: dict[str, list[str]] = {
    "BTR": [f"BTR-{i}" for i in range(1, 6)],
    "COH": [f"COH-{i}" for i in range(1, 9)],
    "FTR": [f"FTR-{i}" for i in range(1, 10)],
    "HBOT": [f"HBOT-{i}" for i in range(1, 7)],
    "LEAN": [f"LEAN-{i}" for i in range(1, 7)],
    "NAUT": [f"NAUT-{i}" for i in range(1, 9)],
    "VBT": [f"VBT-{i}" for i in range(1, 6)],
    "XCOMP": [f"XCOMP-{i}" for i in range(1, 4)],
}

TODO_REF_RE = re.compile(r"Ref:\s*([^`]+)")
TODO_PREFIX_RE = re.compile(r"\b(?:BTR|COH|FTR|HBOT|LEAN|NAUT|VBT|XCOMP)-\d+\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_checked_todo_refs(todo_text: str) -> tuple[set[str], list[str]]:
    ids: set[str] = set()
    errors: list[str] = []
    for idx, line in enumerate(todo_text.splitlines(), start=1):
        token = line.strip()
        if not (token.startswith("- [x]") or token.startswith("- [X]")):
            continue
        ref_match = TODO_REF_RE.search(token)
        if not ref_match:
            continue
        matched = set(TODO_PREFIX_RE.findall(ref_match.group(1)))
        if matched and "Evidence:" not in token:
            errors.append(f"docs/TODO.md:{idx} checked closure item missing Evidence field")
        ids.update(matched)
    return ids, errors


def evaluate_closure(
    *,
    defaults_path: Path,
    todo_path: Path,
    map_path: Path,
) -> list[str]:
    errors: list[str] = []

    for path in (defaults_path, todo_path, map_path):
        if not path.exists():
            errors.append(f"missing file: {path}")
    if errors:
        return errors

    defaults = json.loads(_read(defaults_path))
    families = defaults.get("families")
    if not isinstance(families, dict):
        return ["defaults file missing families object"]

    for family, expected_refs in EXPECTED.items():
        block = families.get(family)
        if not isinstance(block, dict):
            errors.append(f"missing defaults family block: {family}")
            continue
        refs = block.get("refs")
        if refs != expected_refs:
            errors.append(f"{family} refs mismatch")
        if not isinstance(block.get("controls"), dict) or not block["controls"]:
            errors.append(f"{family} controls missing/empty")
        if not isinstance(block.get("acceptance_evidence"), list) or not block["acceptance_evidence"]:
            errors.append(f"{family} acceptance_evidence missing/empty")

    todo_ids, todo_errors = _extract_checked_todo_refs(_read(todo_path))
    errors.extend(todo_errors)

    expected_ids = {req_id for refs in EXPECTED.values() for req_id in refs}
    missing_in_todo = sorted(expected_ids - todo_ids)
    if missing_in_todo:
        errors.append(f"TODO missing checked refs for IDs: {', '.join(missing_in_todo)}")

    map_text = _read(map_path)
    for family in EXPECTED:
        if f"## {family} " not in map_text:
            errors.append(f"execution map missing section for {family}")

    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--defaults",
        default="config/strategy/assimilation_unmapped_p2_defaults.json",
    )
    parser.add_argument("--todo", default="docs/TODO.md")
    parser.add_argument("--map", default="docs/SRS_UNMAPPED_P2_EXECUTION_MAP.md")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors = evaluate_closure(
        defaults_path=Path(args.defaults),
        todo_path=Path(args.todo),
        map_path=Path(args.map),
    )
    payload = {"ok": not errors, "error_count": len(errors), "errors": errors}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

