from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from tools.check_release_provenance import validate_release_provenance


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def test_release_provenance_passes_for_matching_files(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    wheel = dist / "pqts-0.1.0-py3-none-any.whl"
    wheel_bytes = b"wheel-bytes"
    wheel.write_bytes(wheel_bytes)
    wheel_sha = _digest(wheel_bytes)

    metadata = dist / "release_metadata.json"
    metadata.write_text(
        json.dumps({"artifacts": [{"name": wheel.name, "sha256": wheel_sha}]}),
        encoding="utf-8",
    )
    checksums = dist / "SHA256SUMS.txt"
    checksums.write_text(f"{wheel_sha}  {wheel.name}\n", encoding="utf-8")

    errors = validate_release_provenance(
        dist_dir=dist, metadata_path=metadata, checksums_path=checksums
    )
    assert errors == []


def test_release_provenance_flags_checksum_mismatch(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    wheel = dist / "pqts-0.1.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel-bytes")

    metadata = dist / "release_metadata.json"
    metadata.write_text(
        json.dumps({"artifacts": [{"name": wheel.name, "sha256": "deadbeef"}]}),
        encoding="utf-8",
    )
    checksums = dist / "SHA256SUMS.txt"
    checksums.write_text(f"{'0'*64}  {wheel.name}\n", encoding="utf-8")

    errors = validate_release_provenance(
        dist_dir=dist, metadata_path=metadata, checksums_path=checksums
    )
    assert any("metadata=deadbeef" in item for item in errors)
    assert any("checksums=" in item for item in errors)
