from __future__ import annotations

import json
from pathlib import Path

from tools.check_assimilation_66_71_defaults import evaluate_defaults


def test_assimilation_defaults_pass_repo_config() -> None:
    errors = evaluate_defaults(Path("config/strategy/assimilation_66_71_defaults.json"))
    assert errors == []


def test_assimilation_defaults_detects_missing_family(tmp_path: Path) -> None:
    payload = {
        "version": "x",
        "families": {
            "GIPP": {
                "refs": [f"GIPP-{i}" for i in range(1, 9)],
                "controls": {"x": 1},
                "acceptance_evidence": ["ok"],
            }
        },
    }
    cfg = tmp_path / "bad.json"
    cfg.write_text(json.dumps(payload), encoding="utf-8")
    errors = evaluate_defaults(cfg)
    assert any("missing family block: MARIK" in err for err in errors)

