#!/usr/bin/env python3
"""Verify release metadata and checksum provenance before publication."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_checksums(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        checksum = parts[0].strip().lower()
        name = parts[-1].strip()
        mapping[name] = checksum
    return mapping


def validate_release_provenance(
    *,
    dist_dir: Path,
    metadata_path: Path,
    checksums_path: Path,
) -> list[str]:
    errors: list[str] = []
    if not metadata_path.exists():
        return [f"missing metadata file: {metadata_path}"]
    if not checksums_path.exists():
        return [f"missing checksums file: {checksums_path}"]

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    artifacts = list(payload.get("artifacts") or [])
    if not artifacts:
        errors.append("release metadata has no artifacts")

    checksums = _parse_checksums(checksums_path)
    if not checksums:
        errors.append("checksums file has no entries")

    for row in artifacts:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).strip()
        expected_sha = str(row.get("sha256", "")).strip().lower()
        if not name:
            errors.append("metadata artifact missing name")
            continue
        artifact_path = dist_dir / name
        if not artifact_path.exists():
            errors.append(f"metadata artifact not found in dist: {name}")
            continue
        actual_sha = _sha256(artifact_path).lower()
        if expected_sha != actual_sha:
            errors.append(f"sha mismatch for {name}: metadata={expected_sha} actual={actual_sha}")
        checksums_sha = checksums.get(name)
        if checksums_sha is None:
            errors.append(f"checksums missing entry for {name}")
        elif checksums_sha != actual_sha:
            errors.append(f"sha mismatch for {name}: checksums={checksums_sha} actual={actual_sha}")
    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument("--metadata", default="dist/release_metadata.json")
    parser.add_argument("--checksums", default="dist/SHA256SUMS.txt")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors = validate_release_provenance(
        dist_dir=Path(args.dist_dir),
        metadata_path=Path(args.metadata),
        checksums_path=Path(args.checksums),
    )
    if errors:
        for item in errors:
            print(f"FAIL {item}")
        return 2
    print(
        json.dumps(
            {
                "validated": True,
                "dist_dir": args.dist_dir,
                "metadata": args.metadata,
                "checksums": args.checksums,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
