from __future__ import annotations

from tools import check_competitor_revalidation


def test_check_competitor_revalidation_tool_passes_repo_defaults(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["check_competitor_revalidation.py", "--today", "2026-03-10"])
    assert check_competitor_revalidation.main() == 0
