from __future__ import annotations

import json

import pytest

from app.cli_output import run_handler


def test_run_handler_table_mode_returns_handler_code() -> None:
    called = {"count": 0}

    def _handler() -> int:
        called["count"] += 1
        print("hello")
        return 0

    rc = run_handler(command_name="demo", handler=_handler, output_mode="table")
    assert rc == 0
    assert called["count"] == 1


def test_run_handler_json_mode_emits_envelope(capsys: pytest.CaptureFixture[str]) -> None:
    def _handler() -> int:
        print("line-1")
        return 9

    rc = run_handler(command_name="demo", handler=_handler, output_mode="json")
    assert rc == 9
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    payload = json.loads(lines[-1])
    assert payload["ok"] is False
    assert payload["command"] == "demo"
    assert payload["return_code"] == 9
    assert payload["error"] == "command_failed"
    assert payload["stdout"] == ["line-1"]
