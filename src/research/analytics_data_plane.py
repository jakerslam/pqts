"""Local analytical data-plane and storage-tier policy contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DataPlanePolicy:
    local_root: str = "data/lake"
    operational_roots: tuple[str, ...] = ("data/analytics", "data/engine_state.json")
    local_formats: tuple[str, ...] = ("parquet", "jsonl", "csv")


def classify_storage_tier(path: str | Path, policy: DataPlanePolicy | None = None) -> str:
    cfg = policy or DataPlanePolicy()
    token = str(path).replace("\\", "/").strip().lower()
    if token.startswith(str(cfg.local_root).lower()):
        return "local_analytics"
    operational_prefixes = tuple(str(item).lower() for item in cfg.operational_roots)
    if any(token.startswith(prefix) for prefix in operational_prefixes):
        return "operational_state"
    return "unknown"


def validate_storage_tier_boundary(
    *,
    path: str | Path,
    expected_tier: str,
    policy: DataPlanePolicy | None = None,
) -> dict[str, Any]:
    actual = classify_storage_tier(path, policy)
    expected = str(expected_tier).strip().lower()
    if actual != expected:
        raise ValueError(f"storage tier mismatch: expected={expected} actual={actual} path={path}")
    return {"validated": True, "tier": actual, "path": str(path)}


def validate_local_data_format(filename: str, policy: DataPlanePolicy | None = None) -> dict[str, Any]:
    cfg = policy or DataPlanePolicy()
    token = str(filename).strip()
    suffix = token.rsplit(".", 1)[-1].lower() if "." in token else ""
    if suffix not in set(cfg.local_formats):
        raise ValueError(f"unsupported local analytical format: {filename}")
    return {"validated": True, "format": suffix}
