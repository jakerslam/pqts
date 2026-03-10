from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.prepare_release_artifacts import prepare_release_artifacts


def _seed_pyproject(path: Path, version: str) -> None:
    path.write_text(
        f"""
[project]
name = "pqts"
version = "{version}"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _seed_changelog(path: Path, version: str) -> None:
    path.write_text(
        f"""
# Changelog

## [{version}] - 2026-03-10

### Added
- Test release entry.
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_prepare_release_artifacts_writes_metadata_and_checksums(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "pqts-0.1.1.tar.gz").write_text("sdist", encoding="utf-8")
    (dist / "pqts-0.1.1-py3-none-any.whl").write_text("wheel", encoding="utf-8")

    pyproject = tmp_path / "pyproject.toml"
    changelog = tmp_path / "CHANGELOG.md"
    _seed_pyproject(pyproject, "0.1.1")
    _seed_changelog(changelog, "0.1.1")

    checksums = dist / "SHA256SUMS.txt"
    metadata = dist / "release_metadata.json"
    payload = prepare_release_artifacts(
        dist_dir=dist,
        version="0.1.1",
        git_sha="abc123",
        pyproject_path=pyproject,
        changelog_path=changelog,
        checksums_path=checksums,
        metadata_path=metadata,
    )

    assert payload["version"] == "0.1.1"
    assert payload["git_sha"] == "abc123"
    assert int(payload["artifact_count"]) == 2
    assert checksums.exists()
    assert metadata.exists()

    checksum_lines = [line for line in checksums.read_text(encoding="utf-8").splitlines() if line]
    assert len(checksum_lines) == 2
    serialized = json.loads(metadata.read_text(encoding="utf-8"))
    assert serialized["artifact_count"] == 2


def test_prepare_release_artifacts_rejects_version_mismatch(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "pqts-0.1.2.tar.gz").write_text("sdist", encoding="utf-8")

    pyproject = tmp_path / "pyproject.toml"
    changelog = tmp_path / "CHANGELOG.md"
    _seed_pyproject(pyproject, "0.1.1")
    _seed_changelog(changelog, "0.1.2")

    with pytest.raises(ValueError, match="Tag/version mismatch"):
        prepare_release_artifacts(
            dist_dir=dist,
            version="0.1.2",
            git_sha="abc123",
            pyproject_path=pyproject,
            changelog_path=changelog,
            checksums_path=dist / "SHA256SUMS.txt",
            metadata_path=dist / "release_metadata.json",
        )
