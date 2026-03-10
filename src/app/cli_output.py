"""Shared output helpers for CLI command handlers."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from typing import Any, Callable


def run_handler(
    *,
    command_name: str,
    handler: Callable[[], int],
    output_mode: str,
) -> int:
    """Run handler with optional JSON envelope preserving existing stdout output."""
    mode = str(output_mode).strip().lower()
    if mode != "json":
        return int(handler())

    stdout_buffer = io.StringIO()
    try:
        with redirect_stdout(stdout_buffer):
            return_code = int(handler())
        payload: dict[str, Any] = {
            "ok": return_code == 0,
            "command": str(command_name),
            "return_code": int(return_code),
            "stdout": [line for line in stdout_buffer.getvalue().splitlines() if line.strip()],
        }
        if return_code != 0:
            payload["error"] = "command_failed"
        print(json.dumps(payload, sort_keys=True))
        return return_code
    except Exception as exc:  # pragma: no cover - exercised by first-success tests
        payload = {
            "ok": False,
            "command": str(command_name),
            "return_code": 2,
            "error": str(exc),
            "stdout": [line for line in stdout_buffer.getvalue().splitlines() if line.strip()],
        }
        print(json.dumps(payload, sort_keys=True))
        return 2

