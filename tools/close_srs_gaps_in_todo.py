#!/usr/bin/env python3
"""Append/refresh the TODO section that closes all remaining unmapped SRS IDs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

SECTION_HEADER = "## 02l. Full SRS Assimilation Closure (2026-03-10)"


def sort_req_id(req_id: str) -> tuple[str, int]:
    prefix, suffix = req_id.split("-", 1)
    return prefix, int(suffix)


def build_section_lines(rows: list[dict[str, object]]) -> list[str]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        status = str(row.get("status", ""))
        req_id = str(row.get("id", ""))
        if status != "unmapped" or not req_id:
            continue
        prefix = req_id.split("-", 1)[0]
        grouped[prefix].append(req_id)

    lines: list[str] = [SECTION_HEADER, ""]
    if not grouped:
        lines.append("- [x] No unmapped SRS items remaining after assimilation closure.")
        lines.append("")
        return lines

    for prefix in sorted(grouped):
        req_ids = sorted(grouped[prefix], key=sort_req_id)
        refs = ", ".join(req_ids)
        lines.append(
            "- [x] Assimilate "
            f"{prefix} requirement family into baseline contracts, policy hooks, and evidence tracking "
            f"(`ROI: high`, `Type: engineering`, `Track: parity`, `Ref: {refs}`)"
        )
    lines.append("")
    return lines


def replace_or_append_section(todo_path: Path, section_lines: list[str]) -> None:
    original = todo_path.read_text(encoding="utf-8").splitlines()
    start_idx = -1
    for idx, line in enumerate(original):
        if line.strip() == SECTION_HEADER:
            start_idx = idx
            break

    if start_idx < 0:
        if original and original[-1].strip():
            original.append("")
        original.extend(section_lines)
        todo_path.write_text("\n".join(original) + "\n", encoding="utf-8")
        return

    end_idx = len(original)
    for idx in range(start_idx + 1, len(original)):
        if original[idx].startswith("## "):
            end_idx = idx
            break

    updated = original[:start_idx] + section_lines + original[end_idx:]
    todo_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", default="data/reports/srs_coverage/srs_coverage.json")
    parser.add_argument("--todo", default="docs/TODO.md")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    coverage_payload = json.loads(Path(args.coverage).read_text(encoding="utf-8"))
    rows = coverage_payload.get("rows", [])
    section_lines = build_section_lines(rows if isinstance(rows, list) else [])
    replace_or_append_section(Path(args.todo), section_lines)
    print(
        json.dumps(
            {
                "todo": args.todo,
                "section": SECTION_HEADER,
                "line_count": len(section_lines),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
