"""Utilities for validating SRS assimilation coverage."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HEADING_RE = re.compile(r"^###\s+([A-Z]{2,6}-\d+)\s+(.+?)\s*$")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SRS_PATH = REPO_ROOT / "docs" / "SRS.md"
DEFAULT_REGISTRY_PATH = REPO_ROOT / "config" / "srs" / "assimilation_registry.json"


@dataclass(frozen=True)
class AssimilatedRequirement:
    """One requirement row from the assimilation registry."""

    req_id: str
    title: str
    prefix: str
    source_status: str
    assimilation_tier: str
    baseline_hook: str


def parse_srs_requirements(srs_path: Path = DEFAULT_SRS_PATH) -> dict[str, str]:
    """Return {req_id: title} parsed from docs/SRS.md headings."""
    requirements: dict[str, str] = {}
    for line in srs_path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line.strip())
        if not match:
            continue
        req_id = match.group(1)
        if req_id in requirements:
            continue
        requirements[req_id] = match.group(2).strip()
    return requirements


def _iter_registry_rows(registry_path: Path) -> Iterable[dict[str, str]]:
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = payload.get("requirements", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def load_assimilation_registry(
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, AssimilatedRequirement]:
    """Load the registry into a dictionary keyed by requirement ID."""
    out: dict[str, AssimilatedRequirement] = {}
    for row in _iter_registry_rows(registry_path):
        req_id = str(row.get("id", "")).strip()
        if not req_id:
            continue
        out[req_id] = AssimilatedRequirement(
            req_id=req_id,
            title=str(row.get("title", "")).strip(),
            prefix=str(row.get("prefix", "")).strip(),
            source_status=str(row.get("source_status", "")).strip(),
            assimilation_tier=str(row.get("assimilation_tier", "")).strip(),
            baseline_hook=str(row.get("baseline_hook", "")).strip(),
        )
    return out


def summarize_assimilation_registry(
    registry: dict[str, AssimilatedRequirement],
) -> dict[str, object]:
    """Build a compact tier summary from loaded registry rows."""
    tier_counts = Counter(item.assimilation_tier for item in registry.values())
    prefix_counts: dict[str, Counter[str]] = {}
    for item in registry.values():
        counts = prefix_counts.setdefault(item.prefix, Counter())
        counts[item.assimilation_tier] += 1
    return {
        "total": len(registry),
        "tier_counts": dict(tier_counts),
        "prefix_counts": {
            prefix: {
                "core_delivery": counts.get("core_delivery", 0),
                "baseline_contract": counts.get("baseline_contract", 0),
            }
            for prefix, counts in sorted(prefix_counts.items())
        },
    }


def ensure_srs_assimilation_coverage(
    *,
    srs_path: Path = DEFAULT_SRS_PATH,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, object]:
    """Validate that every SRS requirement is represented in the registry."""
    requirements = parse_srs_requirements(srs_path)
    registry = load_assimilation_registry(registry_path)
    missing = sorted(req_id for req_id in requirements if req_id not in registry)
    extra = sorted(req_id for req_id in registry if req_id not in requirements)
    return {
        "total_requirements": len(requirements),
        "registry_rows": len(registry),
        "missing": missing,
        "extra": extra,
        "summary": summarize_assimilation_registry(registry),
    }
