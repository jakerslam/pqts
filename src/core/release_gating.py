"""Release gating with signed build provenance generation and verification."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from core.compliance_security import build_signed_release_manifest, verify_signed_release_manifest


@dataclass(frozen=True)
class ReleaseGateResult:
    passed: bool
    reason: str
    missing_artifacts: list[str]
    manifest_path: str
    verification_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_provenance_bundle(
    *,
    artifacts: Sequence[str],
    output_dir: str,
    signing_key: str,
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "release_manifest.json"
    manifest = build_signed_release_manifest(
        artifacts=artifacts,
        output_path=str(manifest_path),
        signing_key=signing_key,
    )
    metadata = {
        "manifest_path": str(manifest_path),
        "artifact_count": len(list(artifacts)),
        "signature": manifest.get("signature", ""),
    }
    metadata_path = out / "provenance_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "manifest": manifest,
        "manifest_path": str(manifest_path),
        "metadata_path": str(metadata_path),
    }


def evaluate_release_gate(
    *,
    required_artifacts: Sequence[str],
    manifest_path: str,
    signing_key: str,
) -> ReleaseGateResult:
    missing = [str(path) for path in required_artifacts if not Path(path).exists()]
    verification_passed = False
    if Path(manifest_path).exists():
        verification_passed = bool(
            verify_signed_release_manifest(manifest_path=manifest_path, signing_key=signing_key)
        )
    if missing:
        return ReleaseGateResult(
            passed=False,
            reason="required_artifacts_missing",
            missing_artifacts=missing,
            manifest_path=str(manifest_path),
            verification_passed=verification_passed,
        )
    if not verification_passed:
        return ReleaseGateResult(
            passed=False,
            reason="manifest_verification_failed",
            missing_artifacts=[],
            manifest_path=str(manifest_path),
            verification_passed=False,
        )
    return ReleaseGateResult(
        passed=True,
        reason="release_gate_passed",
        missing_artifacts=[],
        manifest_path=str(manifest_path),
        verification_passed=True,
    )
