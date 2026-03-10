from __future__ import annotations

from core.native_migration import (
    MigrationEvidence,
    build_native_release_matrix,
    decide_native_migration,
)


def test_decide_native_migration_uses_jit_first_policy() -> None:
    evidence = MigrationEvidence(
        module="orderbook_sequence",
        latency_ms_p95=75.0,
        throughput_per_sec=80.0,
        cpu_pct=85.0,
        jit_benchmark_gain_pct=10.0,
        mode="live",
    )
    decision = decide_native_migration(evidence)
    assert decision["bottleneck_detected"] is True
    assert decision["should_migrate_native"] is True


def test_build_native_release_matrix_contains_platform_rows() -> None:
    rows = build_native_release_matrix("pqts_hotpath")
    assert len(rows) >= 6
    assert any(row.target == "manylinux_x86_64" for row in rows)
    assert any(row.target == "macos_arm64" for row in rows)
