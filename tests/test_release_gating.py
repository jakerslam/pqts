"""Tests for release-gating provenance generation and verification."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.release_gating import build_provenance_bundle, evaluate_release_gate


def test_release_gate_passes_with_signed_manifest(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_text("payload", encoding="utf-8")
    bundle = build_provenance_bundle(
        artifacts=[str(artifact)],
        output_dir=str(tmp_path / "release"),
        signing_key="test-signing-key",
    )

    result = evaluate_release_gate(
        required_artifacts=[str(artifact)],
        manifest_path=str(bundle["manifest_path"]),
        signing_key="test-signing-key",
    )
    assert result.passed is True
    assert result.verification_passed is True


def test_release_gate_fails_when_artifacts_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.bin"
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    result = evaluate_release_gate(
        required_artifacts=[str(missing)],
        manifest_path=str(manifest),
        signing_key="test-signing-key",
    )
    assert result.passed is False
    assert result.reason == "required_artifacts_missing"


def test_release_gate_fails_when_signature_invalid(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_text("payload", encoding="utf-8")
    bundle = build_provenance_bundle(
        artifacts=[str(artifact)],
        output_dir=str(tmp_path / "release"),
        signing_key="good-key",
    )

    result = evaluate_release_gate(
        required_artifacts=[str(artifact)],
        manifest_path=str(bundle["manifest_path"]),
        signing_key="bad-key",
    )
    assert result.passed is False
    assert result.reason == "manifest_verification_failed"
