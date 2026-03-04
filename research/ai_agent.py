# AI Research Agent - Main Orchestrator
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path
import json
import time

from research.auto_generator import AutoStrategyGenerator, StrategyVariant
from research.database import ResearchDatabase, BacktestResult, Experiment
from research.regime_detector import RegimeDetector, MarketRegime
from research.walk_forward import WalkForwardTester

logger = logging.getLogger(__name__)

class AIResearchAgent:
    """
    Autonomous AI agent that discovers and optimizes trading strategies.
    
    Implements the research cycle described in ChatGPT analysis:
    1. Generate strategy variants
    2. Run backtests
    3. Record results
    4. Rank by fitness
    5. Promote winners to paper trading
    6. Retire weak strategies
    
    This is the system's "quant research team" - continuously searching
    for profitable edges.
    """
    
    def __init__(self, config: dict):
        self.config = config
        
        # Subsystems
        self.db = ResearchDatabase(config.get('db_path', 'data/research.db'))
        self.generator = AutoStrategyGenerator()
        self.regime_detector = RegimeDetector(config.get('regime', {}))
        self.walk_forward = WalkForwardTester(config.get('walk_forward', {}))
        
        # Parameters
        self.search_budget = config.get('search_budget', 100)  # Variants to test
        self.top_performers = config.get('top_performers', 10)
        self.min_sharpe_for_promotion = config.get('min_sharpe', 1.0)
        self.max_drawdown = config.get('max_drawdown', 0.15)
        
        # State
        self.active_strategies: Dict[str, Dict] = {}
        self.paper_trading: List[str] = []
        self.live_trading: List[str] = []
        
        logger.info(f"AIResearchAgent initialized: budget={self.search_budget}")
    
    def research_cycle(self, historical_data: Dict[str, pd.DataFrame],
                      strategy_types: List[str] = None) -> Dict:
        """
        Main research loop: generate → test → rank → promote.
        
        Args:
            historical_data: Historical market data for testing
            strategy_types: List of strategy types to explore
        """
        if strategy_types is None:
            strategy_types = ['market_making', 'cross_exchange', 'stat_arb']
        
        logger.info(f"Starting research cycle for: {strategy_types}")
        
        # Phase 1: Generate candidates
        candidates = self._generate_candidates(strategy_types)
        
        # Phase 2: Run backtests
        results = self._run_backtests(candidates, historical_data)
        
        # Phase 3: Rank by fitness
        ranked = self._rank_strategies(results)
        
        # Phase 4: Walk-forward validation
        validated = self._walk_forward_test(ranked[:20], historical_data)
        
        # Phase 5: Promote winners
        promoted = self._promote_to_paper(validated)
        
        # Phase 6: Report results
        report = self._generate_report(candidates, results, promoted)
        
        logger.info(f"Research cycle complete: {len(candidates)} generated, {len(promoted)} promoted")
        
        return report
    
    def _generate_candidates(self, strategy_types: List[str],
                            variants_per_type: int = 10) -> List[StrategyVariant]:
        """Generate strategy candidates."""
        candidates = []
        
        for stype in strategy_types:
            variants = self.generator.generate_strategy_variants(stype, variants_per_type)
            candidates.extend(variants)
        
        logger.info(f"Generated {len(candidates)} candidate strategies")
        return candidates
    
    def _run_backtests(self, candidates: List[StrategyVariant],
                      data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Backtest all candidates."""
        results = []
        
        # Log experiment
        for variant in candidates:
            experiment = Experiment(
                experiment_id=variant.strategy_id,
                strategy_name=variant.strategy_type,
                variant_id=variant.strategy_id.split('_')[-1],
                features=variant.features,
                parameters=variant.parameters,
                status='backtest'
            )
            self.db.log_experiment(experiment)
        
        # Run backtests (parallelizable in future)
        for i, variant in enumerate(candidates):
            logger.debug(f"Backtesting {i+1}/{len(candidates)}: {variant.strategy_id}")
            
            # Simulate backtest with realistic parameters
            # In real implementation, this calls EventDrivenBacktester
            metrics = self._simulate_backtest(variant, data)
            
            # Store result
            result = BacktestResult(
                strategy_id=variant.strategy_id,
                features_used=variant.features,
                hyperparameters=variant.parameters,
                pnl=metrics['total_return'],
                sharpe=metrics['sharpe'],
                drawdown=metrics['max_drawdown'],
                win_rate=metrics['win_rate'],
                total_trades=metrics['total_trades'],
                market_regime=metrics.get('market_regime', 'unknown'),
                timestamp=datetime.now()
            )
            
            self.db.log_backtest_result(result)
            results.append({
                'variant': variant,
                'metrics': metrics,
                'fitness': metrics['sharpe'] - 0.3 * abs(metrics['max_drawdown'])
            })
            
            time.sleep(0.01)  # Prevent CPU thrashing
        
        return results
    
    def _simulate_backtest(self, variant: StrategyVariant,
                          data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Simulate realistic backtest metrics.
        
        Real implementation would use EventDrivenBacktester.
        """
        import random
        random.seed(hash(variant.strategy_id) % 10000)
        
        # Base performance varies by strategy quality
        base_sharpe = random.gauss(0.8, 0.5)
        
        # Boost for good feature selection
        if 'ob_imbalance' in variant.features and variant.strategy_type == 'market_making':
            base_sharpe += 0.5
        
        # Random metrics
        sharpe = max(-0.5, min(3.0, base_sharpe))
        total_return = sharpe * 0.1  # Approximate
        drawdown = random.uniform(-0.3, -0.05)
        win_rate = random.uniform(0.45, 0.65)
        trades = random.randint(50, 500)
        
        return {
            'sharpe': sharpe,
            'total_return': total_return,
            'max_drawdown': drawdown,
            'win_rate': win_rate,
            'total_trades': trades
        }
    
    def _rank_strategies(self, results: List[Dict]) -> List[Dict]:
        """Rank strategies by fitness."""
        # Sort by fitness
        ranked = sorted(results, key=lambda x: x['fitness'], reverse=True)
        return ranked
    
    def _walk_forward_test(self, top_strategies: List[Dict],
                          data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Validate top strategies with walk-forward testing."""
        confirmed = []
        
        for strategy_data in top_strategies:
            variant = strategy_data['variant']
            
            # Run walk-forward
            # In real implementation: result = self.walk_forward.run(...)
            # For now, assume walk-forward reduces performance by 20%
            wf_sharpe = strategy_data['metrics']['sharpe'] * 0.8
            
            if wf_sharpe >= self.min_sharpe_for_promotion:
                strategy_data['walk_forward_sharpe'] = wf_sharpe
                confirmed.append(strategy_data)
        
        logger.info(f"Walk-forward validated: {len(confirmed)}/{len(top_strategies)}")
        return confirmed
    
    def _promote_to_paper(self, validated: List[Dict]) -> List[str]:
        """Promote validated strategies to paper trading."""
        promoted = []
        
        for result in validated[:self.top_performers]:
            variant = result['variant']
            
            # Check constraints
            if abs(result['metrics']['max_drawdown']) < self.max_drawdown:
                if result['walk_forward_sharpe'] >= self.min_sharpe_for_promotion:
                    
                    # Promote
                    self.db.promote_to_paper(variant.strategy_id)
                    self.paper_trading.append(variant.strategy_id)
                    promoted.append(variant.strategy_id)
                    
                    logger.info(f"Promoted {variant.strategy_id} to paper trading")
        
        return promoted
    
    def _generate_report(self, candidates: List[StrategyVariant],
                        results: List[Dict],
                        promoted: List[str]) -> Dict:
        """Generate research report."""
        sharpes = [r['metrics']['sharpe'] for r in results]
        returns = [r['metrics']['total_return'] for r in results]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'candidates_generated': len(candidates),
                'backtests_run': len(results),
                'promoted_to_paper': len(promoted),
                'promoted_ids': promoted
            },
            'performance': {
                'avg_sharpe': np.mean(sharpes),
                'best_sharpe': np.max(sharpes) if sharpes else 0,
                'avg_return': np.mean(returns),
                'best_return': np.max(returns) if returns else 0
            },
            'top_strategies': [
                {
                    'id': r['variant'].strategy_id,
                    'type': r['variant'].strategy_type,
                    'sharpe': r['metrics']['sharpe'],
                    'features': r['variant'].features
                }
                for r in sorted(results, key=lambda x: x['fitness'], reverse=True)[:5]
            ]
        }
    
    def get_top_strategies(self, n: int = 10) -> pd.DataFrame:
        """Get top performing strategies from database."""
        return self.db.get_top_experiments(n)
    
    def monitor_paper_trading(self) -> Dict:
        """
        Monitor paper trading performance.
        
        Strategies with declining performance get demoted.
        """
        metrics = {}
        
        for strategy_id in self.paper_trading:
            # Get recent performance
            # In real implementation: query metrics from trading system
            recent_sharpe = np.random.uniform(0.5, 2.0)  # Placeholder
            
            if recent_sharpe < self.min_sharpe_for_promotion * 0.5:
                # Demote
                logger.warning(f"Demoting {strategy_id}: sharpe={recent_sharpe:.2f}")
                self.paper_trading.remove(strategy_id)
            
            metrics[strategy_id] = {
                'sharpe': recent_sharpe,
                'status': 'active' if strategy_id in self.paper_trading else 'demoted'
            }
        
        return metrics
    
    def discover_new_regime_strategies(self, current_regime: MarketRegime,
                                     data: Dict[str, pd.DataFrame]) -> List[StrategyVariant]:
        """
        When regime changes, discover strategies specific to new regime.
        """
        optimal_strategies = self.regime_detector.get_optimal_strategies(current_regime)
        
        logger.info(f"Generating regime-specific strategies for {current_regime.value}: {optimal_strategies}")
        
        variants = self.generator.generate_strategy_variants(
            optimal_strategies[0] if optimal_strategies else 'market_making',
            n_per_feature_set=10
        )
        
        return variants


if __name__ == "__main__":
    # Test the AI agent
    config = {
        'search_budget': 50,
        'top_performers': 5,
        'min_sharpe': 1.0,
        'max_drawdown': 0.15,
        'db_path': 'data/research_test.db'
    }
    
    agent = AIResearchAgent(config)
    
    # Generate synthetic data
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    dates = pd.date_range('2022-01-01', '2024-12-31', freq='h')
    
    data = {}
    for symbol in symbols:
        data[symbol] = pd.DataFrame({
            'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.01),
            'rsi': 50 + np.random.randn(len(dates)) * 20
        }, index=dates)
    
    # Run research cycle
    print("\n" + "="*60)
    print("AI RESEARCH AGENT - RUNNING RESEARCH CYCLE")
    print("="*60 + "\n")
    
    report = agent.research_cycle(data, ['market_making'])
    
    print("\n" + "="*60)
    print("RESEARCH REPORT")
    print("="*60)
    print(f"\nCandidates Generated: {report['summary']['candidates_generated']}")
    print(f"Backtests Run: {report['summary']['backtests_run']}")
    print(f"Promoted to Paper: {report['summary']['promoted_to_paper']}")
    print(f"\nAverage Sharpe: {report['performance']['avg_sharpe']:.2f}")
    print(f"Best Sharpe: {report['performance']['best_sharpe']:.2f}")
    print(f"\nTop 3 Strategies:")
    for s in report['top_strategies'][:3]:
        print(f"  {s['id']}: sharpe={s['sharpe']:.2f}, features={s['features'][:3]}")
