from __future__ import annotations

from tools import check_control_plane_contract


def test_check_control_plane_contract_tool_passes_repo_defaults(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["check_control_plane_contract.py"])
    assert check_control_plane_contract.main() == 0
