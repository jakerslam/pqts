from __future__ import annotations

from pathlib import Path

from tools.check_external_validation_evidence import evaluate_external_validation


def test_external_validation_contract_passes_with_required_fields(tmp_path: Path) -> None:
    research = tmp_path / "user_research.md"
    research.write_text(
        "release_window: 2026-03\n"
        "external_beginner_participants: 1\n"
        "external_pro_participants: 2\n"
        "internal_proxy_participants: 0\n",
        encoding="utf-8",
    )
    readme = tmp_path / "README.md"
    readme.write_text("No explicit noob/pro claim.\n", encoding="utf-8")
    assert evaluate_external_validation(user_research_path=research, readme_path=readme) == []


def test_external_validation_flags_missing_fields(tmp_path: Path) -> None:
    research = tmp_path / "user_research.md"
    research.write_text("release_window: 2026-03\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("No explicit noob/pro claim.\n", encoding="utf-8")
    errors = evaluate_external_validation(user_research_path=research, readme_path=readme)
    assert any("external_beginner_participants" in item for item in errors)


def test_external_validation_accepts_bulleted_backticked_fields(tmp_path: Path) -> None:
    research = tmp_path / "user_research.md"
    research.write_text(
        "- `release_window: 2026-03`\n"
        "- `external_beginner_participants: 1`\n"
        "- `external_pro_participants: 1`\n"
        "- `internal_proxy_participants: 2`\n",
        encoding="utf-8",
    )
    readme = tmp_path / "README.md"
    readme.write_text("No explicit noob/pro claim.\n", encoding="utf-8")
    assert evaluate_external_validation(user_research_path=research, readme_path=readme) == []
