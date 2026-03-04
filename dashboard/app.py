# Real-time Trading Dashboard
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

# Page config
st.set_page_config(
    page_title="PQTS Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .positive {
        color: #00cc00;
    }
    .negative {
        color: #ff0000;
    }
</style>
""", unsafe_allow_html=True)

class TradingDashboard:
    """
    Real-time trading dashboard for PQTS.
    Displays portfolio, positions, orders, and performance metrics.
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.analytics_dir = self.data_dir / "analytics"
        
    def load_portfolio_data(self) -> dict:
        """Load current portfolio data"""
        try:
            portfolio_file = self.analytics_dir / "portfolio.json"
            if portfolio_file.exists():
                with open(portfolio_file) as f:
                    return json.load(f)
        except Exception as e:
            st.error(f"Error loading portfolio: {e}")
        
        return {
            "total_equity": 10000.0,
            "cash": 5000.0,
            "positions_value": 5000.0,
            "daily_pnl": 0.0,
            "daily_pnl_pct": 0.0
        }
    
    def load_positions(self) -> pd.DataFrame:
        """Load current positions"""
        try:
            positions_file = self.analytics_dir / "positions.json"
            if positions_file.exists():
                with open(positions_file) as f:
                    data = json.load(f)
                    return pd.DataFrame(data)
        except Exception as e:
            pass
        
        # Sample data for demonstration
        return pd.DataFrame([
            {"symbol": "BTCUSDT", "quantity": 0.5, "avg_entry": 45000, "current": 47000, "pnl": 1000, "pnl_pct": 4.44, "market": "crypto"},
            {"symbol": "ETHUSDT", "quantity": 5.0, "avg_entry": 2800, "current": 3200, "pnl": 2000, "pnl_pct": 14.29, "market": "crypto"},
        ])
    
    def load_orders(self) -> pd.DataFrame:
        """Load recent orders"""
        try:
            orders_file = self.analytics_dir / "orders.json"
            if orders_file.exists():
                with open(orders_file) as f:
                    data = json.load(f)
                    return pd.DataFrame(data)
        except Exception as e:
            pass
        
        # Sample data
        return pd.DataFrame([
            {"timestamp": "2024-01-15 10:30:00", "symbol": "BTCUSDT", "side": "buy", "quantity": 0.1, "price": 45000, "status": "filled"},
            {"timestamp": "2024-01-15 11:45:00", "symbol": "ETHUSDT", "side": "buy", "quantity": 1.0, "price": 2800, "status": "filled"},
        ])
    
    def load_equity_curve(self) -> pd.DataFrame:
        """Load equity curve data"""
        try:
            equity_file = self.analytics_dir / "equity_curve.json"
            if equity_file.exists():
                with open(equity_file) as f:
                    data = json.load(f)
                    return pd.DataFrame(data)
        except Exception as e:
            pass
        
        # Generate sample equity curve
        dates = pd.date_range(start='2024-01-01', end='2024-01-15', freq='H')
        equity = 10000 + (dates - dates[0]).total_seconds() / 3600 * 50 + \
                 pd.Series(range(len(dates))).apply(lambda x: 100 if x % 24 == 0 else 0).cumsum()
        
        return pd.DataFrame({
            'timestamp': dates,
            'equity': equity
        })
    
    def load_performance_metrics(self) -> dict:
        """Load performance metrics"""
        try:
            metrics_file = self.analytics_dir / "performance.json"
            if metrics_file.exists():
                with open(metrics_file) as f:
                    return json.load(f)
        except Exception as e:
            pass
        
        return {
            "total_return_pct": 15.5,
            "sharpe_ratio": 1.45,
            "sortino_ratio": 1.82,
            "max_drawdown_pct": -8.2,
            "win_rate": 58.3,
            "profit_factor": 1.65,
            "avg_trade": 125.50,
            "total_trades": 124,
            "winning_trades": 72,
            "losing_trades": 52
        }
    
    def render_header(self):
        """Render header section"""
        st.markdown('<h1 class="main-header">📈 Protheus Quant Trading System</h1>', 
                   unsafe_allow_html=True)
        st.markdown(f"*Real-time dashboard | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    def render_portfolio_summary(self, portfolio: dict):
        """Render portfolio summary cards"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Equity",
                f"${portfolio.get('total_equity', 0):,.2f}",
                f"{portfolio.get('daily_pnl_pct', 0):.2f}%"
            )
        
        with col2:
            st.metric(
                "Cash",
                f"${portfolio.get('cash', 0):,.2f}"
            )
        
        with col3:
            st.metric(
                "Positions Value",
                f"${portfolio.get('positions_value', 0):,.2f}"
            )
        
        with col4:
            st.metric(
                "Daily P&L",
                f"${portfolio.get('daily_pnl', 0):,.2f}",
                f"{portfolio.get('daily_pnl_pct', 0):.2f}%"
            )
        
        with col5:
            unrealized = portfolio.get('unrealized_pnl', 0)
            st.metric(
                "Unrealized P&L",
                f"${unrealized:,.2f}",
                f"{portfolio.get('unrealized_pnl_pct', 0):.2f}%"
            )
    
    def render_equity_chart(self, equity_df: pd.DataFrame):
        """Render equity curve chart"""
        st.subheader("📊 Equity Curve")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=equity_df['timestamp'],
            y=equity_df['equity'],
            mode='lines',
            name='Equity',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Equity ($)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_positions(self, positions_df: pd.DataFrame):
        """Render positions table"""
        st.subheader("📌 Open Positions")
        
        if not positions_df.empty:
            # Format for display
            display_df = positions_df.copy()
            
            # Color coding for P&L
            def color_pnl(val):
                if isinstance(val, (int, float)):
                    return 'color: green' if val > 0 else 'color: red' if val < 0 else ''
                return ''
            
            st.dataframe(
                display_df.style.applymap(color_pnl, subset=['pnl', 'pnl_pct']),
                use_container_width=True
            )
            
            # Total exposure
            total_long = display_df[display_df['quantity'] > 0]['current'].sum()
            total_short = display_df[display_df['quantity'] < 0]['current'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Long Exposure:** ${total_long:,.2f}")
            with col2:
                st.info(f"**Short Exposure:** ${abs(total_short):,.2f}")
        else:
            st.info("No open positions")
    
    def render_orders(self, orders_df: pd.DataFrame):
        """Render orders table"""
        st.subheader("📋 Recent Orders")
        
        if not orders_df.empty:
            st.dataframe(orders_df, use_container_width=True)
        else:
            st.info("No recent orders")
    
    def render_performance_metrics(self, metrics: dict):
        """Render performance metrics"""
        st.subheader("🎯 Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Return", f"{metrics.get('total_return_pct', 0):.2f}%")
            st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
            st.metric("Sortino Ratio", f"{metrics.get('sortino_ratio', 0):.2f}")
        
        with col2:
            st.metric("Max Drawdown", f"{metrics.get('max_drawdown_pct', 0):.2f}%")
            st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
            st.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
        
        with col3:
            st.metric("Total Trades", metrics.get('total_trades', 0))
            st.metric("Winning Trades", metrics.get('winning_trades', 0))
            st.metric("Losing Trades", metrics.get('losing_trades', 0))
    
    def render_strategy_allocation(self):
        """Render strategy allocation chart"""
        st.subheader("🤖 Strategy Allocation")
        
        strategies = pd.DataFrame({
            'Strategy': ['Scalping', 'Trend Following', 'Mean Reversion', 'ML Ensemble', 'Arbitrage'],
            'Allocation': [30, 25, 20, 15, 10],
            'Active': [True, True, False, True, False]
        })
        
        fig = go.Figure(data=[go.Pie(
            labels=strategies['Strategy'],
            values=strategies['Allocation'],
            hole=.3
        )])
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Strategy status
        st.write("**Strategy Status:**")
        for _, row in strategies.iterrows():
            status = "🟢 Active" if row['Active'] else "🔴 Paused"
            st.write(f"- {row['Strategy']}: {row['Allocation']}% | {status}")
    
    def run(self):
        """Run the dashboard"""
        self.render_header()
        
        # Sidebar
        st.sidebar.title("🔧 Settings")
        st.sidebar.selectbox("Timeframe", ["1H", "4H", "1D", "1W"])
        st.sidebar.selectbox("Market", ["All", "Crypto", "Equities", "Forex"])
        st.sidebar.checkbox("Auto-refresh", value=True)
        
        if st.sidebar.button("🔄 Force Refresh"):
            st.rerun()
        
        # Load data
        portfolio = self.load_portfolio_data()
        positions = self.load_positions()
        orders = self.load_orders()
        equity = self.load_equity_curve()
        metrics = self.load_performance_metrics()
        
        # Main content
        self.render_portfolio_summary(portfolio)
        
        st.divider()
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📌 Positions", "📋 Orders", "⚙️ Configuration"])
        
        with tab1:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                self.render_equity_chart(equity)
            
            with col2:
                self.render_strategy_allocation()
            
            self.render_performance_metrics(metrics)
        
        with tab2:
            self.render_positions(positions)
        
        with tab3:
            self.render_orders(orders)
        
        with tab4:
            st.subheader("⚙️ System Configuration")
            
            st.write("**Risk Settings:**")
            st.json({
                "max_portfolio_risk_pct": 2.0,
                "max_position_risk_pct": 1.0,
                "max_drawdown_pct": 10.0,
                "max_leverage": 2.0
            })
            
            st.write("**Active Markets:**")
            st.json({
                "crypto": {"enabled": True, "exchanges": ["binance", "coinbase"]},
                "equities": {"enabled": True, "broker": "alpaca"},
                "forex": {"enabled": False}
            })


if __name__ == "__main__":
    dashboard = TradingDashboard()
    dashboard.run()
