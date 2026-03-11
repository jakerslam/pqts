#!/usr/bin/env python3
"""Generate a machine-readable assimilation registry for all SRS requirements."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HEADING_RE = re.compile(r"^###\s+([A-Z]{2,6}-\d+)\s+(.+?)\s*$")


def parse_srs_requirements(path: Path) -> list[tuple[str, str, str]]:
    requirements: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line.strip())
        if not match:
            continue
        req_id = match.group(1)
        if req_id in seen:
            continue
        seen.add(req_id)
        title = match.group(2).strip()
        prefix = req_id.split("-", 1)[0]
        requirements.append((req_id, title, prefix))
    return requirements


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--srs", default="docs/SRS.md")
    parser.add_argument("--coverage", default="data/reports/srs_coverage/srs_coverage.json")
    parser.add_argument("--out", default="config/srs/assimilation_registry.json")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    srs_path = Path(args.srs)
    coverage_path = Path(args.coverage)
    out_path = Path(args.out)

    requirements = parse_srs_requirements(srs_path)
    coverage_rows = json.loads(coverage_path.read_text(encoding="utf-8")).get("rows", [])
    status_by_id = {str(row.get("id", "")): str(row.get("status", "unmapped")) for row in coverage_rows}

    generated_at = datetime.now(timezone.utc).isoformat()
    tier_counts: Counter[str] = Counter()
    prefix_counts: dict[str, Counter[str]] = {}
    entries: list[dict[str, str]] = []

    for req_id, title, prefix in requirements:
        source_status = status_by_id.get(req_id, "unmapped")
        tier = "core_delivery" if source_status == "implemented" else "baseline_contract"
        tier_counts[tier] += 1
        prefix_counter = prefix_counts.setdefault(prefix, Counter())
        prefix_counter[tier] += 1
        entries.append(
            {
                "id": req_id,
                "title": title,
                "prefix": prefix,
                "source_status": source_status,
                "assimilation_tier": tier,
                "baseline_hook": f"srs_baseline.{prefix.lower()}",
            }
        )

    payload = {
        "generated_at": generated_at,
        "summary": {
            "total_requirements": len(entries),
            "tier_counts": dict(tier_counts),
        },
        "prefix_summary": {
            prefix: {
                "core_delivery": counts.get("core_delivery", 0),
                "baseline_contract": counts.get("baseline_contract", 0),
            }
            for prefix, counts in sorted(prefix_counts.items())
        },
        "requirements": entries,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(out_path),
                "total_requirements": len(entries),
                "tier_counts": dict(tier_counts),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
