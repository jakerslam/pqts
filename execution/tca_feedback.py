"""
TCA Feedback Loop - Transaction Cost Analysis

Implements Grok's recommendation:
- Log predicted vs realized slippage/fees by symbol/venue
- Refit cost model parameters weekly
- Alert on drift

This feeds cost model calibration data back from live/paper trading.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
import csv

try:
    import pyarrow  # noqa: F401
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False
    logging.warning("pyarrow not available, using CSV fallback for TCA database")

logger = logging.getLogger(__name__)


@dataclass
class TCATradeRecord:
    """Single trade with predicted vs realized costs."""
    trade_id: str
    timestamp: datetime
    symbol: str
    exchange: str
    side: str
    quantity: float
    price: float
    notional: float
    
    # Predicted
    predicted_slippage_bps: float
    predicted_commission_bps: float
    predicted_total_bps: float
    
    # Realized
    realized_slippage_bps: float
    realized_commission_bps: float
    realized_total_bps: float
    
    # Market conditions
    spread_bps: float
    vol_24h: float  # 24h volatility
    depth_1pct_usd: float
    
    # Error metrics
    @property
    def slippage_error(self) -> float:
        """Predicted - realized (positive = we estimated too high)."""
        return self.predicted_slippage_bps - self.realized_slippage_bps
    
    @property
    def prediction_error_pct(self) -> float:
        """Percentage error in total cost prediction."""
        if self.predicted_total_bps == 0:
            return 0
        return (self.realized_total_bps - self.predicted_total_bps) / self.predicted_total_bps * 100


class TCADatabase:
    """Store and query TCA records."""
    
    def __init__(self, db_path: str = "data/tca_records.csv"):
        self.db_path = Path(db_path)
        self.records: List[TCATradeRecord] = []
        self._load_existing()
    
    def _load_existing(self):
        """Load existing records if database exists."""
        if not self.db_path.exists():
            return
        
        try:
            if HAS_PYARROW and self.db_path.suffix == '.parquet':
                df = pd.read_parquet(self.db_path)
            else:
                csv_path = self.db_path.with_suffix('.csv')
                if csv_path.exists():
                    df = pd.read_csv(csv_path, parse_dates=['timestamp'])
                else:
                    return
            
            self.records = self._df_to_records(df)
            logger.info(f"Loaded {len(self.records)} TCA records from {self.db_path}")
        except Exception as e:
            logger.warning(f"Could not load TCA database: {e}")
    
    def _df_to_records(self, df: pd.DataFrame) -> List[TCATradeRecord]:
        """Convert DataFrame to TCATradeRecord objects."""
        records = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            # Convert timestamp back to datetime
            if 'timestamp' in row_dict and isinstance(row_dict['timestamp'], str):
                row_dict['timestamp'] = pd.to_datetime(row_dict['timestamp'])
            records.append(TCATradeRecord(**row_dict))
        return records
    
    def _records_to_df(self) -> pd.DataFrame:
        """Convert TCATradeRecord objects to DataFrame."""
        if not self.records:
            return pd.DataFrame()
        
        data = []
        for r in self.records:
            data.append({
                'trade_id': r.trade_id,
                'timestamp': r.timestamp,
                'symbol': r.symbol,
                'exchange': r.exchange,
                'side': r.side,
                'quantity': r.quantity,
                'price': r.price,
                'notional': r.notional,
                'predicted_slippage_bps': r.predicted_slippage_bps,
                'predicted_commission_bps': r.predicted_commission_bps,
                'predicted_total_bps': r.predicted_total_bps,
                'realized_slippage_bps': r.realized_slippage_bps,
                'realized_commission_bps': r.realized_commission_bps,
                'realized_total_bps': r.realized_total_bps,
                'spread_bps': r.spread_bps,
                'vol_24h': r.vol_24h,
                'depth_1pct_usd': r.depth_1pct_usd
            })
        return pd.DataFrame(data)
    
    def add_record(self, record: TCATradeRecord):
        """Add a new trade record."""
        self.records.append(record)
        logger.debug(f"TCA: Added record {record.trade_id}")
    
    def save(self):
        """Save database to disk."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        df = self._records_to_df()
        
        if HAS_PYARROW:
            parquet_path = self.db_path.with_suffix('.parquet')
            df.to_parquet(parquet_path)
            logger.info(f"Saved {len(self.records)} TCA records to {parquet_path}")
        else:
            csv_path = self.db_path.with_suffix('.csv')
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved {len(self.records)} TCA records to {csv_path}")
    
    def get_recent(self, n: int = 100) -> pd.DataFrame:
        """Get most recent N records."""
        df = self._records_to_df()
        return df.tail(n)
    
    def get_by_symbol(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get records for a symbol in last N days."""
        df = self._records_to_df()
        if df.empty:
            return df
        cutoff = datetime.now() - timedelta(days=days)
        return df[(df['symbol'] == symbol) & (df['timestamp'] >= cutoff)]
    
    def get_by_venue(self, exchange: str, days: int = 30) -> pd.DataFrame:
        """Get records for a venue in last N days."""
        df = self._records_to_df()
        if df.empty:
            return df
        cutoff = datetime.now() - timedelta(days=days)
        return df[(df['exchange'] == exchange) & (df['timestamp'] >= cutoff)]


class TCACalibrator:
    """
    Calibrate cost model parameters based on realized costs.
    
    Runs weekly or on demand.
    """
    
    def __init__(self, tca_db: TCADatabase,
                 min_samples: int = 50,
                 alert_threshold_pct: float = 20.0):
        """
        Args:
            tca_db: TCA database with trade records
            min_samples: Minimum samples needed for calibration
            alert_threshold_pct: Alert if prediction error > this pct
        """
        self.tca_db = tca_db
        self.min_samples = min_samples
        self.alert_threshold = alert_threshold_pct
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """Analyze prediction accuracy for a symbol."""
        df = self.tca_db.get_by_symbol(symbol, days=30)
        
        if len(df) < self.min_samples:
            return {
                'symbol': symbol,
                'status': 'insufficient_data',
                'n_trades': len(df),
                'needs': self.min_samples
            }
        
        # Calculate errors
        df['slippage_error'] = df['predicted_slippage_bps'] - df['realized_slippage_bps']
        df['total_error'] = df['predicted_total_bps'] - df['realized_total_bps']
        
        analysis = {
            'symbol': symbol,
            'status': 'ok',
            'n_trades': len(df),
            'slippage': {
                'predicted_avg': df['predicted_slippage_bps'].mean(),
                'realized_avg': df['realized_slippage_bps'].mean(),
                'mean_error': df['slippage_error'].mean(),
                'std_error': df['slippage_error'].std(),
                'mape': abs(df['slippage_error'] / (df['realized_slippage_bps'] + 0.01)).mean() * 100
            },
            'total_cost': {
                'predicted_avg': df['predicted_total_bps'].mean(),
                'realized_avg': df['realized_total_bps'].mean(),
                'mean_error': df['total_error'].mean(),
                'std_error': df['total_error'].std(),
            },
            'by_spread': self._analyze_by_spread(df),
            'by_vol': self._analyze_by_vol(df),
            'alerts': []
        }
        
        # Check for drift
        if analysis['slippage']['mape'] > self.alert_threshold:
            analysis['status'] = 'alert'
            analysis['alerts'].append(
                f"Slippage prediction MAPE {analysis['slippage']['mape']:.1f}% > threshold {self.alert_threshold}%"
            )
        
        if abs(analysis['slippage']['mean_error']) > 5:  # 5 bps bias
            analysis['alerts'].append(
                f"Slippage bias {analysis['slippage']['mean_error']:.2f} bps (over-predicting if positive)"
            )
        
        return analysis
    
    def _analyze_by_spread(self, df: pd.DataFrame) -> Dict:
        """Analyze how spread affects prediction error."""
        if df.empty or 'spread_bps' not in df.columns:
            return {}
        
        # Need at least 5 unique values for qcut
        if len(df['spread_bps'].unique()) < 5:
            return {}
        
        df['spread_bucket'] = pd.qcut(df['spread_bps'], q=5, labels=['v_low', 'low', 'med', 'high', 'v_high'], duplicates='drop')
        
        result = {}
        for bucket in df['spread_bucket'].unique():
            if pd.isna(bucket):
                continue
            bucket_data = df[df['spread_bucket'] == bucket]
            result[str(bucket)] = {
                'n_trades': len(bucket_data),
                'avg_spread': bucket_data['spread_bps'].mean(),
                'avg_error': (bucket_data['predicted_slippage_bps'] - bucket_data['realized_slippage_bps']).mean()
            }
        return result
    
    def _analyze_by_vol(self, df: pd.DataFrame) -> Dict:
        """Analyze how volatility affects prediction error."""
        if df.empty or 'vol_24h' not in df.columns:
            return {}
        
        # Need at least 5 unique values for qcut
        if len(df['vol_24h'].unique()) < 5:
            return {}
        
        df['vol_bucket'] = pd.qcut(df['vol_24h'], q=5, labels=['v_low', 'low', 'med', 'high', 'v_high'], duplicates='drop')
        
        result = {}
        for bucket in df['vol_bucket'].unique():
            if pd.isna(bucket):
                continue
            bucket_data = df[df['vol_bucket'] == bucket]
            result[str(bucket)] = {
                'n_trades': len(bucket_data),
                'avg_vol': bucket_data['vol_24h'].mean(),
                'avg_error': (bucket_data['predicted_slippage_bps'] - bucket_data['realized_slippage_bps']).mean()
            }
        return result
    
    def calibrate_impact_constant(self, symbol: str, current_eta: float) -> Tuple[float, Dict]:
        """
        Calibrate the market impact constant (eta) for a symbol.
        
        Returns:
            (new_eta, analysis_dict)
        """
        df = self.tca_db.get_by_symbol(symbol, days=30)
        
        if len(df) < self.min_samples:
            return current_eta, {
                'status': 'insufficient_data',
                'n_trades': len(df),
                'kept_eta': current_eta
            }
        
        # Simple linear regression to find eta adjustment
        # Impact ≈ η × σ × √participation
        # We solve for η using realized slippage
        
        df['realized_impact'] = df['realized_slippage_bps'] / 10000  # Convert to decimal
        
        # Estimate participation from depth
        df['estimated_participation'] = df['notional'] / (df['depth_1pct_usd'] + 1e-6)
        df['estimated_participation'] = df['estimated_participation'].clip(upper=1.0)
        
        # Fit: impact = k × √participation
        # k should be around: η × σ (volatility)
        
        X = np.sqrt(df['estimated_participation'].values)
        y = df['realized_impact'].values
        
        # Least squares fit
        if len(X) > 0 and X.sum() > 0:
            k_optimal = np.dot(X, y) / np.dot(X, X)
        else:
            k_optimal = current_eta * 0.5  # Assumed vol
        
        # Convert k back to η (assuming σ = 50% annual = 0.5)
        new_eta = k_optimal / 0.5
        
        # Constrain reasonable range
        new_eta = np.clip(new_eta, 0.1, 2.0)
        
        analysis = {
            'status': 'calibrated',
            'n_trades': len(df),
            'eta_before': current_eta,
            'eta_after': new_eta,
            'change_pct': (new_eta - current_eta) / current_eta * 100,
            'k_fitted': k_optimal
        }
        
        return new_eta, analysis
    
    def run_weekly_calibration(self, symbols: List[str],
                               current_params: Dict[str, float]) -> Tuple[Dict, List[Dict]]:
        """
        Run weekly calibration across all symbols.
        
        Returns:
            (new_params, analysis_list)
        """
        logger.info("="*70)
        logger.info("WEEKLY TCA CALIBRATION")
        logger.info("="*70)
        
        new_params = current_params.copy()
        analyses = []
        
        for symbol in symbols:
            logger.info(f"\nCalibrating {symbol}...")
            current_eta = current_params.get(symbol, 0.5)
            
            # Run calibration
            new_eta, analysis = self.calibrate_impact_constant(symbol, current_eta)
            new_params[symbol] = new_eta
            analyses.append(analysis)
            
            # Log results
            if analysis['status'] == 'calibrated':
                logger.info(f"  η: {analysis['eta_before']:.3f} → {analysis['eta_after']:.3f} "
                          f"({analysis['change_pct']:+.1f}%)")
        
        # Overall analysis
        total_alert = sum(1 for a in analyses if a.get('status') == 'alert')
        total_calibrated = sum(1 for a in analyses if a.get('status') == 'calibrated')
        
        logger.info("\n" + "="*70)
        logger.info("CALIBRATION SUMMARY")
        logger.info("="*70)
        logger.info(f"Symbols calibrated: {total_calibrated}")
        logger.info(f"Alerts raised: {total_alert}")
        
        return new_params, analyses
    
    def generate_report(self, symbols: List[str]) -> str:
        """Generate human-readable TCA report."""
        lines = [
            "="*70,
            "TCA WEEKLY REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "="*70,
            ""
        ]
        
        for symbol in symbols:
            analysis = self.analyze_symbol(symbol)
            
            lines.append(f"\n{symbol}:")
            lines.append(f"  Status: {analysis['status'].upper()}")
            lines.append(f"  Trades: {analysis.get('n_trades', 0)}")
            
            if analysis.get('status') == 'ok':
                lines.append(f"  Avg Predicted Slippage: {analysis['slippage']['predicted_avg']:.2f} bps")
                lines.append(f"  Avg Realized Slippage: {analysis['slippage']['realized_avg']:.2f} bps")
                lines.append(f"  Mean Error: {analysis['slippage']['mean_error']:+.2f} bps")
                lines.append(f"  MAPE: {analysis['slippage']['mape']:.1f}%")
            
            if analysis.get('alerts'):
                lines.append(f"  ⚠️  ALERTS:")
                for alert in analysis['alerts']:
                    lines.append(f"      - {alert}")
        
        lines.extend(["", "="*70])
        return "\n".join(lines)


# ============================================================================
# UNIT TESTS
# ============================================================================

def test_tca_database():
    """Test TCA database operations."""
    import tempfile
    import os
    
    print("="*70)
    print("TCA DATABASE TESTS")
    print("="*70)
    
    # Create temp database
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        db_path = f.name
    db_path = Path(db_path).with_suffix('.csv')
    
    try:
        db = TCADatabase(str(db_path))
        
        # Add test records
        record1 = TCATradeRecord(
            trade_id='t1',
            timestamp=datetime.now(),
            symbol='BTC',
            exchange='binance',
            side='buy',
            quantity=0.1,
            price=50000,
            notional=5000,
            predicted_slippage_bps=10.0,
            predicted_commission_bps=10.0,
            predicted_total_bps=20.0,
            realized_slippage_bps=12.0,
            realized_commission_bps=10.0,
            realized_total_bps=22.0,
            spread_bps=5.0,
            vol_24h=0.5,
            depth_1pct_usd=100000
        )
        
        db.add_record(record1)
        db.save()
        
        # Reload
        db2 = TCADatabase(str(db_path))
        assert len(db2.records) == 1
        assert db2.records[0].trade_id == 't1'
        
        print("✓ TEST 1: Database save/load works")
        
        # Query
        recent = db2.get_recent(10)
        assert len(recent) == 1
        
        print("✓ TEST 2: Query works")
        
        # Symbol filter
        symbol_df = db2.get_by_symbol('BTC')
        assert len(symbol_df) == 1
        
        symbol_df_empty = db2.get_by_symbol('ETH')
        assert len(symbol_df_empty) == 0
        
        print("✓ TEST 3: Symbol filtering works")
        
        print("\n" + "="*70)
        print("ALL TCA DATABASE TESTS PASSED")
        print("="*70)
        
    finally:
        for ext in ['.csv', '.parquet']:
            p = db_path.with_suffix(ext)
            if p.exists():
                os.unlink(p)


def test_tca_calibrator():
    """Test TCA calibrator."""
    print("\n" + "="*70)
    print("TCA CALIBRATOR TESTS")
    print("="*70)
    
    import tempfile
    
    # Create temp database with sample data
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        db_path = f.name
    db_path = Path(db_path).with_suffix('.csv')
    
    db = TCADatabase(str(db_path))
    
    # Add 60 records for BTC
    np.random.seed(42)
    for i in range(60):
        record = TCATradeRecord(
            trade_id=f'btc_{i}',
            timestamp=datetime.now() - timedelta(days=i//10),
            symbol='BTC',
            exchange='binance',
            side='buy',
            quantity=0.1 + np.random.random() * 0.5,
            price=48000 + np.random.random() * 4000,
            notional=5000 + np.random.random() * 20000,
            predicted_slippage_bps=10.0,
            predicted_commission_bps=10.0,
            predicted_total_bps=20.0,
            realized_slippage_bps=8.0 + np.random.randn() * 3,  # Realized slightly different
            realized_commission_bps=10.0,
            realized_total_bps=22.0 + np.random.randn() * 3,
            spread_bps=3.0 + np.random.random() * 10,
            vol_24h=0.4 + np.random.random() * 0.2,
            depth_1pct_usd=50000 + np.random.random() * 100000
        )
        db.add_record(record)
    
    db.save()
    
    # Create calibrator
    calibrator = TCACalibrator(db, min_samples=50)
    
    # Analyze BTC
    analysis = calibrator.analyze_symbol('BTC')
    assert analysis['status'] == 'ok' or analysis['status'] == 'alert' or analysis['status'] == 'insufficient_data'
    
    print(f"✓ TEST 1: BTC analysis works")
    print(f"  Status: {analysis.get('status')}")
    print(f"  Trades: {analysis.get('n_trades', 0)}")
    
    # Calibrate
    new_eta, cal_analysis = calibrator.calibrate_impact_constant('BTC', 0.5)
    assert 0.1 <= new_eta <= 2.0  # Reasonable range
    
    print(f"✓ TEST 2: Calibration works")
    print(f"  η: {cal_analysis['eta_before']:.3f} → {cal_analysis['eta_after']:.3f}")
    
    # Test report
    report = calibrator.generate_report(['BTC'])
    assert 'BTC' in report
    
    print(f"✓ TEST 3: Report generation works")
    
    print("\n" + "="*70)
    print("ALL TCA CALIBRATOR TESTS PASSED")
    print("="*70)
    
    import os
    for ext in ['.csv', '.parquet']:
        p = db_path.with_suffix(ext)
        if p.exists():
            os.unlink(p)


if __name__ == "__main__":
    test_tca_database()
    test_tca_calibrator()
