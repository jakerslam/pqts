"""Deterministic tests for AIResearchAgent constraints and promotion gates."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research.ai_agent import AIResearchAgent
from research.auto_generator import StrategyVariant
from research.database import Experiment


def _historical_data() -> dict[str, pd.DataFrame]:
    index = pd.date_range("2025-01-01", periods=360, freq="h")
    btc = 100.0 + np.linspace(0.0, 8.0, len(index)) + 0.8 * np.sin(np.linspace(0.0, 15.0, len(index)))
    eth = 60.0 + np.linspace(0.0, 4.0, len(index)) + 0.5 * np.cos(np.linspace(0.0, 18.0, len(index)))
    return {
        "BTCUSDT": pd.DataFrame({"close": btc}, index=index),
        "ETHUSDT": pd.DataFrame({"close": eth}, index=index),
    }


def _agent_config(tmp_path: Path) -> dict:
    return {
        "db_path": str(tmp_path / "research.db"),
        "search_budget": 12,
        "top_performers": 3,
        "min_sharpe": 0.2,
        "max_drawdown": 0.35,
        "min_profit_factor": 1.0,
        "min_deflated_sharpe": -1.0,
        "max_pbo": 1.0,
        "walk_forward": {
            "train_years": 1,
            "validate_years": 1,
            "test_years": 1,
            "step_years": 1,
        },
        "capacity": {
            "deployable_capital": 500000.0,
            "max_annual_turnover_notional": 500000000.0,
        },
        "costs": {
            "commission_bps": 6.0,
            "slippage_bps": 8.0,
            "borrow_funding_bps": 3.0,
        },
        "objective": {
            "max_sharpe": 1.5,
            "max_annual_vol": 0.25,
            "annual_turnover": 6.0,
            "cost_per_turnover": 0.0045,
            "target_annual_profit": 1000000.0,
        },
    }


def _log_paper_metrics(agent: AIResearchAgent, strategy_id: str, slippage: float = 10.0) -> None:
    now = datetime.now(timezone.utc)
    for day_offset in range(30):
        agent.record_stage_metrics(
            strategy_id,
            "paper",
            {
                "pnl": 100.0,
                "sharpe": 1.25,
                "drawdown": 0.08,
                "slippage_mape": slippage,
                "kill_switch_triggers": 0,
            },
            timestamp=now - timedelta(days=day_offset),
        )


def test_objective_constraints_block_unrealistic_10x_monthly(tmp_path):
    agent = AIResearchAgent(_agent_config(tmp_path))
    assessment = agent.validate_objective_constraints({"target_monthly_return": 10.0})

    assert assessment["objective_valid"] is False
    assert any("target_monthly_return" in msg for msg in assessment["violations"])


def test_deterministic_backtest_metrics_repeat_exactly(tmp_path):
    agent = AIResearchAgent(_agent_config(tmp_path))
    variant = StrategyVariant(
        strategy_id="market_making_fixed",
        strategy_type="market_making",
        features=["ob_imbalance", "vol_regime"],
        parameters={"spread_bps": 20, "skew_factor": 0.25},
    )
    data = _historical_data()

    first = agent._run_deterministic_backtest(variant, data)
    second = agent._run_deterministic_backtest(variant, data)

    assert np.isclose(first["sharpe"], second["sharpe"])
    assert np.isclose(first["total_return"], second["total_return"])
    assert np.isclose(first["max_drawdown"], second["max_drawdown"])
    assert first["total_trades"] == second["total_trades"]


def test_stage_gate_promotes_paper_to_live_canary(tmp_path):
    agent = AIResearchAgent(_agent_config(tmp_path))
    strategy_id = "mm_gate_pass"

    agent.db.log_experiment(
        Experiment(
            experiment_id=strategy_id,
            strategy_name="market_making",
            variant_id="gate_pass",
            features=["ob_imbalance"],
            parameters={},
            status="paper",
        )
    )
    _log_paper_metrics(agent, strategy_id, slippage=12.0)

    assessment = agent.evaluate_stage_gate(strategy_id, "live_canary")
    assert assessment["passed"] is True
    assert agent.promote_from_stage(strategy_id, "live_canary") is True
    assert agent.db.get_experiment_status(strategy_id) == "live_canary"


def test_stage_gate_blocks_on_slippage_drift(tmp_path):
    agent = AIResearchAgent(_agent_config(tmp_path))
    strategy_id = "mm_gate_block"

    agent.db.log_experiment(
        Experiment(
            experiment_id=strategy_id,
            strategy_name="market_making",
            variant_id="gate_block",
            features=["ob_imbalance"],
            parameters={},
            status="paper",
        )
    )
    _log_paper_metrics(agent, strategy_id, slippage=65.0)

    assessment = agent.evaluate_stage_gate(strategy_id, "live_canary")
    assert assessment["passed"] is False
    assert assessment["checks"]["slippage_mape"] is False


def test_research_cycle_returns_evidence_report(tmp_path):
    config = _agent_config(tmp_path)
    config["search_budget"] = 6
    config["top_performers"] = 2
    config["min_sharpe"] = -1.0
    config["min_deflated_sharpe"] = -2.0
    config["max_drawdown"] = 1.0
    agent = AIResearchAgent(config)

    report = agent.research_cycle(_historical_data(), strategy_types=["market_making"])

    assert report["summary"]["candidates_generated"] <= 6
    assert report["summary"]["backtests_run"] == report["summary"]["candidates_generated"]
    assert "objective" in report
    assert "profit_target_feasibility" in report["objective"]
