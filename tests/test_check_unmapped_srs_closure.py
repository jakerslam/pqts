from __future__ import annotations

import json
from pathlib import Path

from tools.check_unmapped_srs_closure import evaluate_closure


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_unmapped_closure_passes_repo_defaults() -> None:
    errors = evaluate_closure(
        defaults_path=Path("config/strategy/assimilation_unmapped_p2_defaults.json"),
        todo_path=Path("docs/TODO.md"),
        map_path=Path("docs/SRS_UNMAPPED_P2_EXECUTION_MAP.md"),
    )
    assert errors == []


def test_unmapped_closure_flags_missing_refs(tmp_path: Path) -> None:
    defaults = {
        "families": {
            "BTR": {"refs": [f"BTR-{i}" for i in range(1, 6)], "controls": {"x": 1}, "acceptance_evidence": ["ok"]},
            "COH": {"refs": [f"COH-{i}" for i in range(1, 9)], "controls": {"x": 1}, "acceptance_evidence": ["ok"]},
            "FTR": {"refs": [f"FTR-{i}" for i in range(1, 10)], "controls": {"x": 1}, "acceptance_evidence": ["ok"]},
            "HBOT": {"refs": [f"HBOT-{i}" for i in range(1, 7)], "controls": {"x": 1}, "acceptance_evidence": ["ok"]},
            "LEAN": {"refs": [f"LEAN-{i}" for i in range(1, 7)], "controls": {"x": 1}, "acceptance_evidence": ["ok"]},
            "NAUT": {"refs": [f"NAUT-{i}" for i in range(1, 9)], "controls": {"x": 1}, "acceptance_evidence": ["ok"]},
            "VBT": {"refs": [f"VBT-{i}" for i in range(1, 6)], "controls": {"x": 1}, "acceptance_evidence": ["ok"]},
            "XCOMP": {"refs": [f"XCOMP-{i}" for i in range(1, 4)], "controls": {"x": 1}, "acceptance_evidence": ["ok"]},
        }
    }
    defaults_path = tmp_path / "defaults.json"
    defaults_path.write_text(json.dumps(defaults), encoding="utf-8")

    todo_path = tmp_path / "TODO.md"
    _write(
        todo_path,
        "- [x] partial (`Ref: BTR-1`, `Evidence: x`)\n",
    )

    map_path = tmp_path / "MAP.md"
    _write(
        map_path,
        "\n".join(
            [
                "## BTR ",
                "## COH ",
                "## FTR ",
                "## HBOT ",
                "## LEAN ",
                "## NAUT ",
                "## VBT ",
                "## XCOMP ",
            ]
        ),
    )

    errors = evaluate_closure(
        defaults_path=defaults_path,
        todo_path=todo_path,
        map_path=map_path,
    )
    assert any("TODO missing checked refs for IDs" in err for err in errors)

