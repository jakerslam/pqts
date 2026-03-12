#!/usr/bin/env python3
"""Prepare and validate semantic release metadata artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
try:
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore
from typing import Any


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_project_version(pyproject_path: str | Path) -> str:
    payload = tomllib.loads(Path(pyproject_path).read_text(encoding="utf-8"))
    project = payload.get("project", {})
    if not isinstance(project, dict):
        return ""
    return str(project.get("version", "")).strip()


def _validate_version(version: str) -> None:
    token = str(version).strip()
    if not SEMVER_RE.match(token):
        raise ValueError(f"Version must be semantic (X.Y.Z), got: {version!r}")


def _validate_changelog(changelog_path: str | Path, version: str) -> None:
    target = f"## [{version}]"
    text = Path(changelog_path).read_text(encoding="utf-8")
    if target not in text:
        raise ValueError(f"Missing changelog section: {target}")


def _iter_release_files(dist_dir: str | Path) -> list[Path]:
    path = Path(dist_dir)
    if not path.exists():
        return []
    files = [item for item in path.iterdir() if item.is_file() and item.name not in {"SHA256SUMS.txt", "release_metadata.json"}]
    return sorted(files, key=lambda p: p.name)


def build_release_metadata(
    *,
    dist_dir: str | Path,
    version: str,
    git_sha: str,
) -> dict[str, Any]:
    files = _iter_release_files(dist_dir)
    artifacts: list[dict[str, Any]] = []
    for file_path in files:
        artifacts.append(
            {
                "name": file_path.name,
                "size_bytes": int(file_path.stat().st_size),
                "sha256": _sha256_file(file_path),
            }
        )

    return {
        "version": str(version),
        "git_sha": str(git_sha),
        "build_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def write_checksums_file(metadata: dict[str, Any], output_path: str | Path) -> Path:
    lines: list[str] = []
    for item in metadata.get("artifacts", []):
        if not isinstance(item, dict):
            continue
        checksum = str(item.get("sha256", "")).strip()
        name = str(item.get("name", "")).strip()
        if checksum and name:
            lines.append(f"{checksum}  {name}")

    path = Path(output_path)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def write_metadata_file(metadata: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def prepare_release_artifacts(
    *,
    dist_dir: str | Path,
    version: str,
    git_sha: str,
    pyproject_path: str | Path,
    changelog_path: str | Path,
    checksums_path: str | Path,
    metadata_path: str | Path,
) -> dict[str, Any]:
    _validate_version(version)

    project_version = _load_project_version(pyproject_path)
    if project_version != str(version):
        raise ValueError(
            f"Tag/version mismatch: pyproject version {project_version!r} != release {version!r}"
        )

    _validate_changelog(changelog_path, version)
    metadata = build_release_metadata(dist_dir=dist_dir, version=version, git_sha=git_sha)
    if int(metadata.get("artifact_count", 0)) <= 0:
        raise ValueError("No release artifacts found in dist directory.")

    write_checksums_file(metadata, checksums_path)
    write_metadata_file(metadata, metadata_path)
    return metadata


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument("--version", required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--pyproject", default="pyproject.toml")
    parser.add_argument("--changelog", default="CHANGELOG.md")
    parser.add_argument("--checksums", default="dist/SHA256SUMS.txt")
    parser.add_argument("--metadata", default="dist/release_metadata.json")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    metadata = prepare_release_artifacts(
        dist_dir=args.dist_dir,
        version=args.version,
        git_sha=args.git_sha,
        pyproject_path=args.pyproject,
        changelog_path=args.changelog,
        checksums_path=args.checksums,
        metadata_path=args.metadata,
    )
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
