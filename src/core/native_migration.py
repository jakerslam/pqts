"""Native hot-path migration trigger and release-matrix contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MigrationEvidence:
    module: str
    latency_ms_p95: float
    throughput_per_sec: float
    cpu_pct: float
    jit_benchmark_gain_pct: float
    mode: str


@dataclass(frozen=True)
class NativeReleaseArtifact:
    target: str
    python_version: str
    wheel_tag: str
    native_module: str


def decide_native_migration(evidence: MigrationEvidence) -> dict[str, Any]:
    bottleneck = (
        evidence.latency_ms_p95 > 50.0
        or evidence.cpu_pct > 80.0
        or evidence.throughput_per_sec < 100.0
    )
    jit_sufficient = evidence.jit_benchmark_gain_pct >= 20.0
    should_migrate = bottleneck and not jit_sufficient
    return {
        "module": evidence.module,
        "bottleneck_detected": bool(bottleneck),
        "jit_sufficient": bool(jit_sufficient),
        "should_migrate_native": bool(should_migrate),
        "mode": evidence.mode,
    }


def build_native_release_matrix(native_module: str) -> list[NativeReleaseArtifact]:
    targets = [
        ("manylinux_x86_64", "cp311", "cp311-manylinux_x86_64"),
        ("manylinux_x86_64", "cp312", "cp312-manylinux_x86_64"),
        ("macos_arm64", "cp311", "cp311-macosx_11_0_arm64"),
        ("macos_arm64", "cp312", "cp312-macosx_11_0_arm64"),
        ("windows_amd64", "cp311", "cp311-win_amd64"),
        ("windows_amd64", "cp312", "cp312-win_amd64"),
    ]
    return [
        NativeReleaseArtifact(
            target=target,
            python_version=py,
            wheel_tag=wheel,
            native_module=native_module,
        )
        for target, py, wheel in targets
    ]
