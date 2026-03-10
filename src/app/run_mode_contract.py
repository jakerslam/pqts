"""Deployment run-mode contract for environment-driven entrypoints."""

from __future__ import annotations

import os
import shlex
import sys
from dataclasses import dataclass
from typing import Mapping

SUPPORTED_RUN_MODES = {"engine", "api", "stream", "dashboard"}


@dataclass(frozen=True)
class RunModePlan:
    mode: str
    command: list[str]
    required_env: tuple[str, ...]
    missing_env: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.missing_env


def resolve_run_mode(env: Mapping[str, str] | None = None) -> str:
    source = env or os.environ
    token = str(source.get("PQTS_RUN_MODE") or source.get("RUN_MODE") or "engine").strip().lower()
    if token not in SUPPORTED_RUN_MODES:
        return "engine"
    return token


def required_env_for_mode(mode: str) -> tuple[str, ...]:
    normalized = str(mode).strip().lower()
    if normalized == "api":
        return ("PQTS_API_TOKENS",)
    return ()


def build_run_mode_plan(env: Mapping[str, str] | None = None) -> RunModePlan:
    source = env or os.environ
    mode = resolve_run_mode(source)
    required = required_env_for_mode(mode)
    missing = tuple(name for name in required if not str(source.get(name, "")).strip())
    python = str(sys.executable)
    if mode == "api":
        host = str(source.get("PQTS_API_HOST", "0.0.0.0")).strip() or "0.0.0.0"
        port = str(source.get("PQTS_API_PORT", "8000")).strip() or "8000"
        command = [
            python,
            "-m",
            "uvicorn",
            "services.api.app:app",
            "--host",
            host,
            "--port",
            port,
        ]
    elif mode == "stream":
        config = str(source.get("PQTS_CONFIG", "config/paper.yaml")).strip() or "config/paper.yaml"
        cycles = str(source.get("PQTS_STREAM_WORKER_CYCLES", "0")).strip() or "0"
        sleep_seconds = str(source.get("PQTS_STREAM_WORKER_SLEEP_SECONDS", "1.0")).strip() or "1.0"
        command = [
            python,
            "scripts/run_shadow_stream_worker.py",
            "--config",
            config,
            "--cycles",
            cycles,
            "--sleep-seconds",
            sleep_seconds,
        ]
    elif mode == "dashboard":
        command = [python, "src/dashboard/start.py"]
    else:
        config = str(source.get("PQTS_CONFIG", "config/paper.yaml")).strip() or "config/paper.yaml"
        extra = shlex.split(str(source.get("PQTS_ENGINE_ARGS", "")).strip())
        command = [python, "main.py", config, *extra]
    return RunModePlan(
        mode=mode,
        command=command,
        required_env=required,
        missing_env=missing,
    )
