from __future__ import annotations

import json
from pathlib import Path

from tools import check_surface_contracts


def test_surface_contract_tool_passes(tmp_path: Path, monkeypatch) -> None:
    contract = {
        "engine_id": "core",
        "surfaces": [
            {
                "name": "studio",
                "surface_type": "studio",
                "framework": "dash",
                "entrypoint": "studio.py",
                "consumes_control_plane": True,
                "active": True,
            },
            {
                "name": "core",
                "surface_type": "core",
                "framework": "python-cli",
                "entrypoint": "core.py",
                "consumes_control_plane": True,
                "active": True,
            },
        ],
        "action_mappings": [
            {
                "action": "pause",
                "ui_route": "/pause",
                "cli_command": "pqts run",
                "api_endpoint": "/v1/operator/pause",
            }
        ],
    }
    contract_path = tmp_path / "surface_contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    compose_path = tmp_path / "docker-compose.yml"
    compose_path.write_text("services:\n  dashboard:\n    command: python src/dashboard/start.py\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "check_surface_contracts.py",
            "--contract",
            str(contract_path),
            "--compose",
            str(compose_path),
        ],
    )
    assert check_surface_contracts.main() == 0
