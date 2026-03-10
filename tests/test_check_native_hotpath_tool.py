from __future__ import annotations

from tools import check_native_hotpath


def test_check_native_hotpath_tool_passes_on_repo_defaults(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["check_native_hotpath.py"])
    assert check_native_hotpath.main() == 0
