from __future__ import annotations

from app.run_mode_contract import build_run_mode_plan, resolve_run_mode


def test_resolve_run_mode_defaults_to_engine() -> None:
    mode = resolve_run_mode({})
    assert mode == "engine"


def test_build_run_mode_plan_engine_command() -> None:
    plan = build_run_mode_plan({"PQTS_RUN_MODE": "engine", "PQTS_CONFIG": "config/paper.yaml"})
    assert plan.mode == "engine"
    assert plan.valid is True
    assert "main.py" in " ".join(plan.command)


def test_build_run_mode_plan_api_requires_tokens() -> None:
    plan = build_run_mode_plan({"PQTS_RUN_MODE": "api", "PQTS_API_PORT": "8081"})
    assert plan.mode == "api"
    assert plan.valid is False
    assert "PQTS_API_TOKENS" in plan.missing_env


def test_build_run_mode_plan_api_command_when_tokens_present() -> None:
    plan = build_run_mode_plan(
        {
            "PQTS_RUN_MODE": "api",
            "PQTS_API_TOKENS": "viewer:viewer",
            "PQTS_API_HOST": "127.0.0.1",
            "PQTS_API_PORT": "8082",
        }
    )
    assert plan.mode == "api"
    assert plan.valid is True
    assert plan.command[:4] == [plan.command[0], "-m", "uvicorn", "services.api.app:app"]
    assert "--port" in plan.command
    assert "8082" in plan.command


def test_build_run_mode_plan_stream_command() -> None:
    plan = build_run_mode_plan({"PQTS_RUN_MODE": "stream", "PQTS_STREAM_WORKER_CYCLES": "5"})
    assert plan.mode == "stream"
    assert plan.valid is True
    assert "scripts/run_shadow_stream_worker.py" in " ".join(plan.command)
    assert "5" in plan.command
