from __future__ import annotations

import json
from pathlib import Path

from tools.check_external_beta_framework import evaluate_external_beta_framework


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_external_beta_framework_passes_with_current_window_entry(tmp_path: Path) -> None:
    registry = _write(
        tmp_path / "registry.json",
        {
            "schema_version": "1",
            "cohorts": [
                {
                    "release_window": "2026-03",
                    "status": "planned",
                    "external_beginner_participants": 0,
                    "external_pro_participants": 0,
                    "internal_proxy_participants": 2,
                    "channels": ["discord"],
                }
            ],
        },
    )
    user_research = tmp_path / "research.md"
    user_research.write_text("- `release_window: 2026-03`\n", encoding="utf-8")
    errors = evaluate_external_beta_framework(
        registry_path=registry,
        user_research_path=user_research,
    )
    assert errors == []


def test_external_beta_framework_flags_missing_current_window(tmp_path: Path) -> None:
    registry = _write(
        tmp_path / "registry.json",
        {
            "schema_version": "1",
            "cohorts": [
                {
                    "release_window": "2026-02",
                    "status": "completed",
                    "external_beginner_participants": 1,
                    "external_pro_participants": 1,
                    "internal_proxy_participants": 1,
                    "channels": ["x"],
                }
            ],
        },
    )
    user_research = tmp_path / "research.md"
    user_research.write_text("- `release_window: 2026-03`\n", encoding="utf-8")
    errors = evaluate_external_beta_framework(
        registry_path=registry,
        user_research_path=user_research,
    )
    assert any("missing cohort entry for current release_window" in item for item in errors)
