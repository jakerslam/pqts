# Walk-Forward Testing Framework
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WalkForwardWindow:
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    test_start: datetime
    test_end: datetime

class WalkForwardTester:
    """
    Walk-forward testing to prevent overfitting.
    
    Critical for production: Strategies that work in-sample but fail out-of-sample
    are worthless. Walk-forward simulates how strategies would perform rolling
    forward in time.
    
    Standard approach:
    Train: 2019-2022
    Validate: 2023
    Test: 2024
    
    Then roll forward and repeat.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.train_years = config.get('train_years', 3)
        self.validate_years = config.get('validate_years', 1)
        self.test_years = config.get('test_years', 1)
        self.step_years = config.get('step_years', 1)
        
        logger.info(f"WalkForwardTester: train={self.train_years}y, validate={self.validate_years}y, test={self.test_years}y")
    
    def generate_windows(self, start_date: datetime, end_date: datetime) -> List[WalkForwardWindow]:
        """Generate non-overlapping windows for walk-forward testing."""
        windows = []
        
        current = start_date
        window_years = self.train_years + self.validate_years + self.test_years
        
        while True:
            train_start = current
            train_end = train_start + timedelta(days=self.train_years*365)
            
            validate_start = train_end
            validate_end = validate_start + timedelta(days=self.validate_years*365)
            
            test_start = validate_end
            test_end = test_start + timedelta(days=self.test_years*365)
            
            if test_end > end_date:
                break
            
            window = WalkForwardWindow(
                train_start=train_start,
                train_end=train_end,
                validation_start=validate_start,
                validation_end=validate_end,
                test_start=test_start,
                test_end=test_end
            )
            
            windows.append(window)
            current += timedelta(days=self.step_years*365)
        
        logger.info(f"Generated {len(windows)} walk-forward windows")
        return windows
    
    def run_walk_forward(self, strategy_factory: Callable,
                        data: Dict[str, pd.DataFrame],
                        windows: List[WalkForwardWindow]) -> Dict:
        """
        Run strategy through all walk-forward windows.
        
        Args:
            strategy_factory: Function that creates strategy instance
            data: Historical data
            windows: List of time windows
        """
        results = []
        
        for i, window in enumerate(windows):
            logger.info(f"Window {i+1}/{len(windows)}")
            
            # Train phase
            logger.info(f"  Training: {window.train_start.date()} to {window.train_end.date()}")
            train_strategy = strategy_factory()
            train_data = self._slice_data(data, window.train_start, window.train_end)
            
            # Train strategy (if trainable)
            if hasattr(train_strategy, 'train'):
                train_strategy.train(train_data)
            
            # Validation phase
            logger.info(f"  Validation: {window.validation_start.date()} to {window.validation_end.date()}")
            validation_data = self._slice_data(data, window.validation_start, window.validation_end)
            val_metrics = self._evaluate(train_strategy, validation_data)
            
            # Hyperparameter tuning on validation
            if hasattr(train_strategy, 'tune_hyperparameters'):
                tuned_strategy = train_strategy.tune_hyperparameters(validation_data)
            else:
                tuned_strategy = train_strategy
            
            # Test phase (out-of-sample)
            logger.info(f"  Test: {window.test_start.date()} to {window.test_end.date()}")
            test_data = self._slice_data(data, window.test_start, window.test_end)
            test_metrics = self._evaluate(tuned_strategy, test_data)
            
            results.append({
                'window': i,
                'train_period': f"{window.train_start.date()} to {window.train_end.date()}",
                'validation_sharpe': val_metrics.get('sharpe', 0),
                'test_sharpe': test_metrics.get('sharpe', 0),
                'validation_return': val_metrics.get('total_return', 0),
                'test_return': test_metrics.get('total_return', 0),
                'validation_drawdown': val_metrics.get('max_drawdown', 0),
                'test_drawdown': test_metrics.get('max_drawdown', 0),
                'metrics': test_metrics
            })
        
        # Aggregate results
        aggregate = self._aggregate_results(results)
        
        logger.info(f"Walk-forward complete. Avg Sharpe: {aggregate['avg_sharpe']:.2f}")
        
        return {
            'window_results': results,
            'aggregate': aggregate,
            'consistency_score': aggregate['consistency_score']
        }
    
    def _slice_data(self, data: Dict[str, pd.DataFrame],
                   start: datetime, end: datetime) -> Dict[str, pd.DataFrame]:
        """Slice data to time window."""
        sliced = {}
        for symbol, df in data.items():
            mask = (df.index >= start) & (df.index <= end)
            sliced[symbol] = df[mask]
        return sliced
    
    def _evaluate(self, strategy, data: Dict[str, pd.DataFrame]) -> Dict:
        """Run backtest and return metrics."""
        # This would call the event-driven backtester
        # For now, placeholder
        return {
            'sharpe': np.random.uniform(0.5, 2.0),
            'total_return': np.random.uniform(-0.1, 0.3),
            'max_drawdown': np.random.uniform(-0.2, -0.05),
            'trades': 100
        }
    
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate results across windows."""
        sharpes = [r['test_sharpe'] for r in results]
        returns = [r['test_return'] for r in results]
        drawdowns = [r['test_drawdown'] for r in results]
        
        # Consistency: do results degrade over time?
        consistency = 1 - abs(np.std(sharpes) / (np.mean(sharpes) + 0.01))
        
        return {
            'avg_sharpe': np.mean(sharpes),
            'sharpe_std': np.std(sharpes),
            'min_sharpe': np.min(sharpes),
            'max_sharpe': np.max(sharpes),
            'avg_return': np.mean(returns),
            'avg_drawdown': np.mean(drawdowns),
            'consistency_score': consistency
        }


if __name__ == "__main__":
    # Test
    tester = WalkForwardTester({
        'train_years': 2,
        'validate_years': 1,
        'test_years': 1,
        'step_years': 1
    })
    
    start = datetime(2019, 1, 1)
    end = datetime(2024, 12, 31)
    
    windows = tester.generate_windows(start, end)
    
    print(f"\nGenerated {len(windows)} windows:")
    for w in windows:
        print(f"  Train: {w.train_start.year}-{w.train_end.year}, "
              f"Val: {w.validation_start.year}, "
              f"Test: {w.test_start.year}")
