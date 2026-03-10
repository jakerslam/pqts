"""Proof-as-product artifact pipeline and trust classification gates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ProofArtifact:
    artifact_id: str
    artifact_type: str
    result_class: str
    reproducible_command: str
    provenance_ref: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProofArtifactPipeline:
    def __init__(self) -> None:
        self.artifacts: list[ProofArtifact] = []

    def publish(self, *, artifact_id: str, artifact_type: str, result_class: str, command: str, provenance_ref: str) -> ProofArtifact:
        artifact = ProofArtifact(
            artifact_id=str(artifact_id),
            artifact_type=str(artifact_type),
            result_class=str(result_class),
            reproducible_command=str(command),
            provenance_ref=str(provenance_ref),
            created_at=_utc_now_iso(),
        )
        self._validate_artifact(artifact)
        self.artifacts.append(artifact)
        return artifact

    @staticmethod
    def _validate_artifact(artifact: ProofArtifact) -> None:
        if not artifact.reproducible_command.strip():
            raise ValueError("reproducible_command is required")
        if not artifact.provenance_ref.strip():
            raise ValueError("provenance_ref is required")
        if artifact.result_class not in {"verified", "reference", "diagnostic_only", "unverified"}:
            raise ValueError(f"unsupported result_class: {artifact.result_class}")

    def write_manifest(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": _utc_now_iso(),
            "artifact_count": len(self.artifacts),
            "artifacts": [row.to_dict() for row in self.artifacts],
        }
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return out


def evaluate_trust_classification(*, has_reproducible_evidence: bool, requested_class: str) -> str:
    token = str(requested_class).strip().lower()
    if token in {"verified", "reference"} and not has_reproducible_evidence:
        return "unverified"
    if token not in {"verified", "reference", "diagnostic_only", "unverified"}:
        return "unverified"
    return token
