"""
Test suite for kill switches.

Production-grade tests for risk overlay system.

Run: pytest tests/test_kill_switches.py -v
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from risk.kill_switches import (
    RiskLimits, KillSwitchMonitor, RiskDecision, RiskState,
    PortfolioState, TradingEngine
)


class TestKillSwitchMonitor:
    """Test suite for kill switch monitoring."""
    
    @pytest.fixture
    def limits(self):
        """Standard risk limits for testing."""
        return RiskLimits(
            max_daily_loss_pct=0.02,      # 2%
            max_drawdown_pct=0.10,        # 10%
            max_gross_leverage=2.0,       # 2x
            max_order_notional=50000,     # $50k
            max_slippage_bps=50           # 50 bps
        )
    
    @pytest.fixture
    def monitor(self, limits):
        """Kill switch monitor with test limits and capital injected."""
        monitor = KillSwitchMonitor(limits)
        monitor.set_capital(100000.0, source="test_fixture")
        return monitor
    
    @pytest.fixture
    def portfolio_normal(self):
        """Normal portfolio state."""
        return PortfolioState(
            timestamp=datetime.now(),
            positions={'BTC': 0.5},
            prices={'BTC': 50000},
            total_pnl=1000,
            unrealized_pnl=500,
            realized_pnl=500,
            gross_exposure=25000,
            net_exposure=25000,
            leverage=0.5,
            open_orders=[],
            pending_cancels=[]
        )
    
    @pytest.fixture
    def portfolio_high_lev(self):
        """High leverage portfolio state."""
        return PortfolioState(
            timestamp=datetime.now(),
            positions={'BTC': 2.5},
            prices={'BTC': 50000},
            total_pnl=0,
            unrealized_pnl=0,
            realized_pnl=0,
            gross_exposure=125000,
            net_exposure=125000,
            leverage=2.5,
            open_orders=[],
            pending_cancels=[]
        )
    
    @pytest.fixture
    def portfolio_crash(self):
        """Portfolio in crash scenario."""
        return PortfolioState(
            timestamp=datetime.now(),
            positions={'BTC': 1.0},
            prices={'BTC': 40000},  # 20% down
            total_pnl=-12000,
            unrealized_pnl=-12000,
            realized_pnl=0,
            gross_exposure=40000,
            net_exposure=40000,
            leverage=1.0,
            open_orders=[{'id': 'ord1'}, {'id': 'ord2'}],
            pending_cancels=[]
        )
    
    @pytest.fixture
    def strategy_returns(self):
        """Sample strategy returns."""
        return {
            'strat1': np.random.randn(30) * 0.02,
            'strat2': np.random.randn(30) * 0.01,
            'strat3': np.random.randn(30) * 0.015
        }
    
    def test_initial_state(self, monitor):
        """Test monitor initializes correctly."""
        assert not monitor.kill_switch_active
        assert monitor.kill_reason == ""
        assert monitor.current_drawdown == 0.0
    
    def test_daily_loss_no_trigger(self, monitor, portfolio_normal):
        """Test daily loss check with normal P&L."""
        monitor.daily_pnl = 1000  # Profit
        is_triggered, reason = monitor.check_daily_loss()
        assert not is_triggered
        assert reason == ""
    
    def test_daily_loss_trigger(self, monitor, portfolio_normal):
        """Test daily loss limit triggers correctly."""
        monitor.daily_pnl = -2500  # 2.5% loss on 100k
        is_triggered, reason = monitor.check_daily_loss()
        assert is_triggered
        assert "2.50%" in reason
        assert "2.00%" in reason
    
    def test_drawdown_no_trigger(self, monitor, portfolio_normal):
        """Test drawdown check with normal levels."""
        monitor.peak_portfolio_value = 105000
        monitor.current_drawdown = 0.05  # 5%
        is_triggered, reason = monitor.check_drawdown()
        assert not is_triggered
    
    def test_drawdown_trigger(self, monitor, portfolio_normal):
        """Test drawdown limit triggers correctly."""
        monitor.peak_portfolio_value = 110000
        monitor.current_drawdown = 0.12  # 12%
        is_triggered, reason = monitor.check_drawdown()
        assert is_triggered
        assert "12.00%" in reason
        assert "10.00%" in reason
    
    def test_leverage_no_trigger(self, monitor, portfolio_normal):
        """Test leverage check with normal leverage."""
        is_triggered, reason = monitor.check_leverage(portfolio_normal)
        assert not is_triggered
    
    def test_leverage_trigger(self, monitor, portfolio_high_lev):
        """Test leverage limit triggers correctly."""
        is_triggered, reason = monitor.check_leverage(portfolio_high_lev)
        assert is_triggered
        assert "2.50x" in reason
        assert "2.00x" in reason
    
    def test_slippage_no_trigger(self, monitor):
        """Test slippage check with normal levels."""
        monitor.last_slippages.extend([0.0001, 0.0002, 0.0001])  # 1-2 bps
        is_triggered, reason = monitor.check_slippage()
        assert not is_triggered
    
    def test_slippage_trigger(self, monitor):
        """Test slippage limit triggers correctly."""
        # Need at least slippage_lookback_trade (default 20) entries
        monitor.last_slippages.extend([0.006] * 25)  # 60 bps (over 50 bps limit)
        is_triggered, reason = monitor.check_slippage()
        assert is_triggered
        assert "60" in reason or "0.006" in reason
        assert "50" in reason or "0.005" in reason
    
    def test_evaluate_all_allow(self, monitor, portfolio_normal, strategy_returns):
        """Test all-clear evaluates to ALLOW."""
        state = monitor.evaluate_all(
            portfolio_normal,
            strategy_returns,
            np.random.randn(30) * 1000
        )
        assert state.decision == RiskDecision.ALLOW
        assert state.reason == "All clear"
        assert not monitor.kill_switch_active
    
    def test_evaluate_all_flatten(self, monitor, portfolio_crash, strategy_returns):
        """Test crash scenario triggers FLATTEN."""
        # Simulate large losses
        monitor.daily_pnl = -2500
        monitor.peak_portfolio_value = 110000
        monitor.current_drawdown = 0.12
        
        state = monitor.evaluate_all(
            portfolio_crash,
            strategy_returns,
            [-5000] * 30  # Large negative changes
        )
        
        assert state.decision == RiskDecision.FLATTEN
        assert "Daily loss" in state.reason or "Drawdown" in state.reason
        assert monitor.kill_switch_active


class TestTradingEngine:
    """Test suite for trading engine integration."""
    
    @pytest.fixture
    def engine(self):
        """Trading engine with standard limits and capital injected."""
        limits = RiskLimits(
            max_daily_loss_pct=0.02,
            max_drawdown_pct=0.10,
            max_gross_leverage=2.0
        )
        engine = TradingEngine(limits)
        engine.risk_monitor.set_capital(100000.0, source='test_fixture')
        return engine
    
    @pytest.fixture
    def portfolio(self):
        """Normal portfolio."""
        return PortfolioState(
            timestamp=datetime.now(),
            positions={'BTC': 0.5},
            prices={'BTC': 50000},
            total_pnl=0,
            unrealized_pnl=0,
            realized_pnl=0,
            gross_exposure=25000,
            net_exposure=25000,
            leverage=0.5,
            open_orders=[],
            pending_cancels=[]
        )
    
    @pytest.fixture
    def portfolio_orders(self):
        """Portfolio with open orders."""
        return PortfolioState(
            timestamp=datetime.now(),
            positions={'BTC': 0.5},
            prices={'BTC': 50000},
            total_pnl=0,
            unrealized_pnl=0,
            realized_pnl=0,
            gross_exposure=25000,
            net_exposure=25000,
            leverage=0.5,
            open_orders=[
                {'id': 'ord1'},
                {'id': 'ord2'},
                {'id': 'ord3'}
            ],
            pending_cancels=[]
        )
    
    def test_pre_trade_check_allow(self, engine, portfolio):
        """Test normal conditions allow order."""
        decision, state = engine.pre_trade_check(
            {'notional': 1000},
            portfolio,
            {'s1': np.random.randn(30)},
            np.random.randn(30) * 100
        )
        assert decision == RiskDecision.ALLOW
    
    def test_no_orders_after_flatten(self, engine, portfolio):
        """Test no orders accepted after flatten."""
        # Trigger flatten
        state = engine.manual_kill('test')
        
        # Try to place order
        result = engine.place_order({'notional': 1000}, state)
        assert not result
    
    def test_manual_flatten(self, engine, portfolio):
        """Test manual flatten triggers correctly."""
        state = engine.manual_kill('manual emergency')
        
        assert state.decision == RiskDecision.FLATTEN
        assert 'manual emergency' in state.reason
        assert engine.is_flattening
    
    def test_orders_cancelled_on_flatten(self, engine, portfolio_orders):
        """Test open orders are cancelled on flatten."""
        # Set up so flatten will trigger
        engine.risk_monitor.daily_pnl = -2500
        engine.risk_monitor.peak_portfolio_value = 100000
        engine.risk_monitor.current_drawdown = 0.12
        
        # Trigger flatten
        engine.manual_kill('test')
        engine._initiate_flatten(portfolio_orders)
        
        # Check orders were cancelled
        assert len(engine.cancelled_orders) == 3
        assert 'ord1' in engine.cancelled_orders
    
    def test_reset_after_kill(self, engine, portfolio):
        """Test reset functionality."""
        # Trigger flatten
        engine.manual_kill('test')
        assert engine.is_flattening
        
        # Reset
        engine.reset()
        assert not engine.is_flattening
        assert not engine.is_halted
        assert not engine.risk_monitor.kill_switch_active


class TestIntegration:
    """Integration tests for full system."""
    
    def test_complete_flow_allow(self):
        """Test complete flow from order to execution with ALLOW."""
        limits = RiskLimits(max_daily_loss_pct=0.02)
        engine = TradingEngine(limits)
        engine.risk_monitor.set_capital(100000.0, source='test')
        
        portfolio = PortfolioState(
            timestamp=datetime.now(),
            positions={},
            prices={'BTC': 50000},
            total_pnl=0,
            unrealized_pnl=0,
            realized_pnl=0,
            gross_exposure=0,
            net_exposure=0,
            leverage=0,
            open_orders=[],
            pending_cancels=[]
        )
        
        # Check risk
        decision, state = engine.pre_trade_check(
            {'notional': 5000},
            portfolio,
            {},
            [0] * 30
        )
        
        assert decision == RiskDecision.ALLOW
        
        # Place order
        result = engine.place_order({'notional': 5000}, state)
        assert result
        assert engine.order_count == 1
    
    def test_crash_triggers_flatten_one_tick(self):
        """
        CRITICAL TEST: Simulate 10-sigma crash and verify FLATTEN in one tick.
        
        This is the acceptance criteria from Grok's spec.
        """
        limits = RiskLimits(
            max_daily_loss_pct=0.02,
            max_drawdown_pct=0.10,
            max_gross_leverage=2.0
        )
        engine = TradingEngine(limits)
        engine.risk_monitor.set_capital(100000.0, source='test')  # INJECT CAPITAL
        
        # Simulate crash scenario
        engine.risk_monitor.daily_pnl = -2500  # 2.5% loss
        engine.risk_monitor.peak_portfolio_value = 110000
        engine.risk_monitor.current_drawdown = 0.12  # 12% drawdown
        
        portfolio = PortfolioState(
            timestamp=datetime.now(),
            positions={'BTC': 1.0},
            prices={'BTC': 40000},  # 20% down from 50k
            total_pnl=-12000,
            unrealized_pnl=-12000,
            realized_pnl=0,
            gross_exposure=40000,
            net_exposure=40000,
            leverage=1.0,
            open_orders=[{'id': 'o1'}, {'id': 'o2'}],
            pending_cancels=[]
        )
        
        # One tick risk check
        decision, state = engine.pre_trade_check(
            {'notional': 1000},
            portfolio,
            {'s1': np.random.randn(30) * 0.05},  # High vol
            [-5000] * 30  # Large negative changes
        )
        
        # Verify FLATTEN triggered in one tick
        assert decision == RiskDecision.FLATTEN
        assert engine.is_flattening
        
        # Verify orders cannot be placed
        result = engine.place_order({'notional': 100}, state)
        assert not result
    
    def test_deterministic_triggers(self):
        """Test that triggers are deterministic and reproducible."""
        limits = RiskLimits(max_daily_loss_pct=0.02)
        
        # Create two identical engines
        engine1 = TradingEngine(limits)
        engine2 = TradingEngine(limits)
        
        # INJECT CAPITAL BEFORE ANY CHECKS
        engine1.risk_monitor.set_capital(100000.0, source='test')
        engine2.risk_monitor.set_capital(100000.0, source='test')
        
        # Set identical crash state
        for engine in [engine1, engine2]:
            engine.risk_monitor.daily_pnl = -2500
            engine.risk_monitor.peak_portfolio_value = 100000
            engine.risk_monitor.current_drawdown = 0.11
        
        portfolio = PortfolioState(
            timestamp=datetime.now(),
            positions={},
            prices={'BTC': 50000},
            total_pnl=-11000,
            unrealized_pnl=-11000,
            realized_pnl=0,
            gross_exposure=0,
            net_exposure=0,
            leverage=0,
            open_orders=[],
            pending_cancels=[]
        )
        
        # Same checks on both
        d1, s1 = engine1.pre_trade_check(
            {'notional': 1000}, portfolio, {}, [0]*30
        )
        d2, s2 = engine2.pre_trade_check(
            {'notional': 1000}, portfolio, {}, [0]*30
        )
        
        # Deterministic
        assert d1 == d2
        assert s1.reason == s2.reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
