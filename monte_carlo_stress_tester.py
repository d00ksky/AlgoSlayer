#!/usr/bin/env python3
"""
Monte Carlo Simulation & Stress Testing for AlgoSlayer
Simulates thousands of market scenarios to test robustness
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

from scipy import stats
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor, as_completed
import json

class MarketScenarioGenerator:
    """Generate realistic market scenarios using Monte Carlo"""
    
    def __init__(self):
        self.historical_data = None
        self.market_regimes = {
            'bull': {'drift': 0.08, 'volatility': 0.15, 'crash_prob': 0.02},
            'bear': {'drift': -0.05, 'volatility': 0.25, 'crash_prob': 0.08},
            'sideways': {'drift': 0.02, 'volatility': 0.18, 'crash_prob': 0.05},
            'volatile': {'drift': 0.03, 'volatility': 0.35, 'crash_prob': 0.12}
        }
        
    def load_historical_data(self, symbol: str = 'RTX', years: int = 10):
        """Load historical data to calibrate scenarios"""
        import yfinance as yf
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        
        if not data.empty:
            self.historical_data = data
            logger.info(f"✅ Loaded {len(data)} days of {symbol} historical data")
            self._calibrate_parameters()
        else:
            logger.error(f"❌ Failed to load data for {symbol}")
            
    def _calibrate_parameters(self):
        """Calibrate market parameters from historical data"""
        returns = self.historical_data['Close'].pct_change().dropna()
        
        # Basic statistics
        annual_drift = returns.mean() * 252
        annual_vol = returns.std() * np.sqrt(252)
        
        # Regime detection
        vol_threshold = returns.std() * 1.5
        high_vol_periods = returns.rolling(20).std() > vol_threshold
        
        crash_events = returns < returns.quantile(0.01)
        crash_frequency = crash_events.sum() / len(returns) * 252  # Annualized
        
        logger.info(f"📊 Calibrated parameters:")
        logger.info(f"  Annual drift: {annual_drift:.2%}")
        logger.info(f"  Annual volatility: {annual_vol:.2%}")
        logger.info(f"  Crash frequency: {crash_frequency:.2f} events/year")
        
        # Update market regimes based on historical data
        self.market_regimes['calibrated'] = {
            'drift': annual_drift,
            'volatility': annual_vol,
            'crash_prob': crash_frequency / 252
        }
        
    def generate_price_paths(self, n_simulations: int = 1000, 
                           days: int = 252, regime: str = 'calibrated') -> np.ndarray:
        """Generate Monte Carlo price paths"""
        
        if regime not in self.market_regimes:
            regime = 'calibrated'
            
        params = self.market_regimes[regime]
        
        # Initialize arrays
        price_paths = np.zeros((n_simulations, days + 1))
        price_paths[:, 0] = 100  # Start at $100
        
        dt = 1/252  # Daily time step
        
        for sim in range(n_simulations):
            for day in range(1, days + 1):
                # Basic GBM
                random_shock = np.random.normal(0, 1)
                
                # Add jump risk (crashes)
                jump = 0
                if np.random.random() < params['crash_prob']:
                    jump = np.random.normal(-0.1, 0.05)  # Average -10% crash
                    
                # Price evolution
                drift = params['drift'] * dt
                diffusion = params['volatility'] * np.sqrt(dt) * random_shock
                
                price_paths[sim, day] = price_paths[sim, day-1] * np.exp(
                    drift + diffusion + jump
                )
                
        logger.info(f"✅ Generated {n_simulations} price paths ({days} days each)")
        return price_paths
        
    def generate_volatility_paths(self, n_simulations: int = 1000, 
                                days: int = 252) -> np.ndarray:
        """Generate stochastic volatility paths"""
        
        # Heston-like model parameters
        kappa = 2.0  # Mean reversion speed
        theta = 0.04  # Long-term variance
        sigma_v = 0.3  # Vol of vol
        
        vol_paths = np.zeros((n_simulations, days + 1))
        vol_paths[:, 0] = theta  # Start at long-term variance
        
        dt = 1/252
        
        for sim in range(n_simulations):
            for day in range(1, days + 1):
                dW = np.random.normal(0, np.sqrt(dt))
                
                # Ensure non-negative variance
                current_vol = max(0.01, vol_paths[sim, day-1])
                
                vol_paths[sim, day] = current_vol + kappa * (theta - current_vol) * dt + \
                                     sigma_v * np.sqrt(current_vol) * dW
                                     
        return np.sqrt(vol_paths)  # Return volatility, not variance

class StressTester:
    """Comprehensive stress testing framework"""
    
    def __init__(self):
        self.stress_scenarios = {
            'black_monday_1987': {
                'name': 'Black Monday 1987',
                'shock': -0.226,  # -22.6% in one day
                'duration': 1,
                'recovery_days': 60
            },
            'dotcom_crash_2000': {
                'name': 'Dot-com Crash 2000-2002',
                'shock': -0.49,  # -49% peak to trough
                'duration': 500,
                'recovery_days': 1500
            },
            'financial_crisis_2008': {
                'name': 'Financial Crisis 2008',
                'shock': -0.54,  # -54% peak to trough
                'duration': 365,
                'recovery_days': 1800
            },
            'covid_crash_2020': {
                'name': 'COVID Crash 2020',
                'shock': -0.34,  # -34% in 33 days
                'duration': 33,
                'recovery_days': 150
            },
            'flash_crash_2010': {
                'name': 'Flash Crash 2010',
                'shock': -0.09,  # -9% in minutes
                'duration': 1,
                'recovery_days': 2
            }
        }
        
    def apply_stress_scenario(self, base_prices: np.ndarray, 
                            scenario: str, start_day: int = 50) -> np.ndarray:
        """Apply a specific stress scenario to price paths"""
        
        if scenario not in self.stress_scenarios:
            logger.warning(f"Unknown scenario: {scenario}")
            return base_prices
            
        scenario_data = self.stress_scenarios[scenario]
        stressed_prices = base_prices.copy()
        
        shock = scenario_data['shock']
        duration = scenario_data['duration']
        recovery_days = scenario_data['recovery_days']
        
        n_sims, n_days = stressed_prices.shape
        
        if start_day + duration + recovery_days > n_days:
            logger.warning(f"Scenario too long for price paths")
            return base_prices
            
        for sim in range(n_sims):
            # Apply initial shock
            if duration == 1:
                # Single day crash
                stressed_prices[sim, start_day] *= (1 + shock)
            else:
                # Gradual decline
                daily_shock = shock / duration
                for day in range(start_day, start_day + duration):
                    stressed_prices[sim, day] *= (1 + daily_shock)
                    
            # Recovery phase (gradual)
            if recovery_days > 0:
                recovery_per_day = -shock / recovery_days
                for day in range(start_day + duration, 
                               min(start_day + duration + recovery_days, n_days)):
                    recovery_factor = recovery_per_day * 0.5  # Slower recovery
                    stressed_prices[sim, day] *= (1 + recovery_factor)
                    
        logger.info(f"✅ Applied {scenario_data['name']} stress scenario")
        return stressed_prices

class OptionsBacktestSimulator:
    """Simulate options backtesting under various scenarios"""
    
    def __init__(self):
        self.strategies = {
            'conservative': {'min_confidence': 0.75, 'max_risk': 0.10},
            'moderate': {'min_confidence': 0.70, 'max_risk': 0.15}, 
            'aggressive': {'min_confidence': 0.65, 'max_risk': 0.20},
            'swing': {'min_confidence': 0.60, 'max_risk': 0.15},
            'volatility': {'min_confidence': 0.60, 'max_risk': 0.20}
        }
        
    def simulate_strategy_performance(self, price_paths: np.ndarray, 
                                    vol_paths: np.ndarray,
                                    strategy: str = 'swing') -> Dict:
        """Simulate strategy performance across all price paths"""
        
        if strategy not in self.strategies:
            strategy = 'swing'
            
        config = self.strategies[strategy]
        n_sims, n_days = price_paths.shape
        
        results = {
            'total_returns': [],
            'max_drawdowns': [],
            'sharpe_ratios': [],
            'win_rates': [],
            'trade_counts': []
        }
        
        for sim in range(n_sims):
            sim_result = self._simulate_single_path(
                price_paths[sim], vol_paths[sim], config
            )
            
            for key in results.keys():
                results[key].append(sim_result[key])
                
        # Convert to numpy arrays and calculate statistics
        keys_list = list(results.keys())  # Create a copy of keys
        for key in keys_list:
            arr = np.array(results[key])
            results[f'{key}_mean'] = np.mean(arr)
            results[f'{key}_std'] = np.std(arr)
            results[f'{key}_5th'] = np.percentile(arr, 5)
            results[f'{key}_95th'] = np.percentile(arr, 95)
            
        return results
        
    def _simulate_single_path(self, prices: np.ndarray, 
                            vols: np.ndarray, config: Dict) -> Dict:
        """Simulate strategy on a single price path"""
        
        capital = 10000
        positions = []
        returns = []
        
        # Simple trading logic
        for day in range(20, len(prices) - 30):  # Need lookback and lookahead
            current_price = prices[day]
            current_vol = vols[day]
            
            # Generate synthetic confidence based on recent performance
            recent_returns = prices[day-10:day] / prices[day-11:day-1] - 1
            momentum = np.mean(recent_returns)
            vol_percentile = (current_vol - np.mean(vols[:day])) / np.std(vols[:day])
            
            # Simplified confidence calculation
            confidence = 0.5 + momentum * 5 + vol_percentile * 0.1
            confidence = max(0, min(1, confidence))
            
            # Trading decision
            if confidence > config['min_confidence'] and len(positions) < 3:
                # Enter position
                risk = min(config['max_risk'], confidence * 0.3)
                position_size = capital * risk
                
                # Simulate option outcome (simplified)
                entry_price = current_price
                exit_day = day + np.random.randint(5, 21)  # 5-20 days
                
                if exit_day < len(prices):
                    exit_price = prices[exit_day]
                    
                    # Simplified option P&L
                    stock_return = (exit_price / entry_price) - 1
                    option_return = stock_return * 3  # Simplified leverage
                    
                    # Option decay
                    days_held = exit_day - day
                    decay_factor = 1 - (days_held / 30) * 0.1
                    option_return *= decay_factor
                    
                    pnl = position_size * option_return
                    capital += pnl
                    returns.append(option_return)
                    
                    positions.append({
                        'entry_day': day,
                        'exit_day': exit_day,
                        'pnl': pnl,
                        'return': option_return
                    })
                    
        # Calculate metrics
        if len(returns) > 0:
            total_return = (capital / 10000) - 1
            win_rate = sum(1 for r in returns if r > 0) / len(returns)
            
            # Simplified Sharpe ratio
            if len(returns) > 1:
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252/10)
            else:
                sharpe = 0
                
            # Max drawdown
            equity_curve = [10000]
            for pos in positions:
                equity_curve.append(equity_curve[-1] + pos['pnl'])
                
            running_max = np.maximum.accumulate(equity_curve)
            drawdowns = (np.array(equity_curve) - running_max) / running_max
            max_drawdown = np.min(drawdowns)
            
        else:
            total_return = 0
            win_rate = 0
            sharpe = 0
            max_drawdown = 0
            
        return {
            'total_returns': total_return,
            'max_drawdowns': max_drawdown,
            'sharpe_ratios': sharpe,
            'win_rates': win_rate,
            'trade_counts': len(positions)
        }

def run_comprehensive_stress_testing():
    """Run comprehensive Monte Carlo stress testing"""
    
    logger.info("🚀 STARTING COMPREHENSIVE STRESS TESTING")
    logger.info("="*80)
    
    # 1. Initialize components
    scenario_gen = MarketScenarioGenerator()
    stress_tester = StressTester()
    backtest_sim = OptionsBacktestSimulator()
    
    # 2. Load and calibrate
    logger.info("📊 Loading historical data and calibrating...")
    scenario_gen.load_historical_data('RTX', years=10)
    
    # 3. Generate base scenarios
    logger.info("\n🎲 Generating Monte Carlo scenarios...")
    
    scenarios = {}
    
    # Normal market conditions
    scenarios['normal'] = scenario_gen.generate_price_paths(
        n_simulations=500, days=252, regime='calibrated'
    )
    
    # Bull market
    scenarios['bull'] = scenario_gen.generate_price_paths(
        n_simulations=500, days=252, regime='bull'
    )
    
    # Bear market
    scenarios['bear'] = scenario_gen.generate_price_paths(
        n_simulations=500, days=252, regime='bear'
    )
    
    # High volatility
    scenarios['volatile'] = scenario_gen.generate_price_paths(
        n_simulations=500, days=252, regime='volatile'
    )
    
    # Generate volatility paths for all scenarios
    vol_scenarios = {}
    for name in scenarios.keys():
        vol_scenarios[name] = scenario_gen.generate_volatility_paths(
            n_simulations=500, days=252
        )
        
    # 4. Apply stress scenarios
    logger.info("\n💥 Applying historical stress scenarios...")
    
    stress_scenarios = {}
    stress_vol_scenarios = {}
    
    for stress_name in stress_tester.stress_scenarios.keys():
        logger.info(f"  Applying {stress_name}...")
        
        stress_scenarios[stress_name] = stress_tester.apply_stress_scenario(
            scenarios['normal'], stress_name, start_day=50
        )
        
        # Use same volatility but with stress adjustments
        stress_vol = vol_scenarios['normal'].copy()
        stress_vol[:, 50:100] *= 2  # Double volatility during stress
        stress_vol_scenarios[stress_name] = stress_vol
        
    # 5. Test all strategies across all scenarios
    logger.info("\n🧪 Testing strategies across all scenarios...")
    
    all_results = {}
    
    test_scenarios = {**scenarios, **stress_scenarios}
    test_vol_scenarios = {**vol_scenarios, **stress_vol_scenarios}
    
    for strategy in backtest_sim.strategies.keys():
        logger.info(f"\n🎯 Testing {strategy} strategy...")
        
        strategy_results = {}
        
        for scenario_name, price_paths in test_scenarios.items():
            vol_paths = test_vol_scenarios[scenario_name]
            
            logger.info(f"  - {scenario_name}")
            
            results = backtest_sim.simulate_strategy_performance(
                price_paths, vol_paths, strategy
            )
            
            strategy_results[scenario_name] = results
            
        all_results[strategy] = strategy_results
        
    # 6. Generate comprehensive report
    logger.info("\n📊 Generating stress test report...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'data/stress_test_report_{timestamp}.json'
    
    # Prepare summary statistics
    summary = {}
    
    for strategy, strategy_results in all_results.items():
        summary[strategy] = {}
        
        for scenario, results in strategy_results.items():
            summary[strategy][scenario] = {
                'avg_return': results['total_returns_mean'],
                'return_std': results['total_returns_std'],
                'worst_case_5th': results['total_returns_5th'],
                'best_case_95th': results['total_returns_95th'],
                'avg_sharpe': results['sharpe_ratios_mean'],
                'avg_win_rate': results['win_rates_mean'],
                'avg_max_drawdown': results['max_drawdowns_mean'],
                'survival_rate': sum(1 for r in results['total_returns'] if r > -0.5) / len(results['total_returns'])
            }
            
    # Save detailed results
    with open(report_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
        
    logger.info(f"💾 Detailed results saved: {report_file}")
    
    # 7. Print executive summary
    logger.info("\n" + "="*80)
    logger.info("STRESS TEST EXECUTIVE SUMMARY")
    logger.info("="*80)
    
    for strategy in summary.keys():
        logger.info(f"\n🎯 {strategy.upper()} STRATEGY:")
        logger.info("-" * 40)
        
        strategy_data = summary[strategy]
        
        # Overall statistics
        all_returns = []
        all_sharpes = []
        all_survivals = []
        
        for scenario, data in strategy_data.items():
            all_returns.append(data['avg_return'])
            all_sharpes.append(data['avg_sharpe'])
            all_survivals.append(data['survival_rate'])
            
        logger.info(f"Average Return Across All Scenarios: {np.mean(all_returns):+.1%}")
        logger.info(f"Average Sharpe Across All Scenarios: {np.mean(all_sharpes):.2f}")
        logger.info(f"Average Survival Rate: {np.mean(all_survivals):.1%}")
        
        # Worst and best scenarios
        worst_scenario = min(strategy_data.items(), key=lambda x: x[1]['avg_return'])
        best_scenario = max(strategy_data.items(), key=lambda x: x[1]['avg_return'])
        
        logger.info(f"\nWorst Scenario: {worst_scenario[0]} ({worst_scenario[1]['avg_return']:+.1%})")
        logger.info(f"Best Scenario: {best_scenario[0]} ({best_scenario[1]['avg_return']:+.1%})")
        
        # Stress test performance
        stress_scenarios_data = {k: v for k, v in strategy_data.items() 
                               if k in stress_tester.stress_scenarios.keys()}
        
        if stress_scenarios_data:
            stress_returns = [data['avg_return'] for data in stress_scenarios_data.values()]
            stress_survivals = [data['survival_rate'] for data in stress_scenarios_data.values()]
            
            logger.info(f"\nStress Test Performance:")
            logger.info(f"  Average Return in Crashes: {np.mean(stress_returns):+.1%}")
            logger.info(f"  Survival Rate in Crashes: {np.mean(stress_survivals):.1%}")
            
    # 8. Strategy ranking
    logger.info("\n" + "="*80)
    logger.info("STRATEGY RANKING BY RISK-ADJUSTED RETURNS")
    logger.info("="*80)
    
    strategy_scores = []
    
    for strategy, strategy_data in summary.items():
        # Calculate composite score
        avg_return = np.mean([data['avg_return'] for data in strategy_data.values()])
        avg_sharpe = np.mean([data['avg_sharpe'] for data in strategy_data.values()])
        avg_survival = np.mean([data['survival_rate'] for data in strategy_data.values()])
        
        # Weighted score (return 40%, sharpe 30%, survival 30%)
        composite_score = (avg_return * 0.4 + 
                          (avg_sharpe / 3) * 0.3 +  # Normalize Sharpe
                          avg_survival * 0.3)
        
        strategy_scores.append((strategy, composite_score, avg_return, avg_sharpe, avg_survival))
        
    # Sort by composite score
    strategy_scores.sort(key=lambda x: x[1], reverse=True)
    
    logger.info("\nRank | Strategy    | Score  | Avg Return | Avg Sharpe | Survival")
    logger.info("-" * 65)
    
    for i, (strategy, score, ret, sharpe, survival) in enumerate(strategy_scores, 1):
        logger.info(f"{i:4d} | {strategy:11} | {score:6.3f} | {ret:+9.1%} | {sharpe:10.2f} | {survival:8.1%}")
        
    logger.info("\n🎉 COMPREHENSIVE STRESS TESTING COMPLETE!")
    logger.info(f"📊 Tested {len(backtest_sim.strategies)} strategies")
    logger.info(f"🎲 Across {len(test_scenarios)} market scenarios")
    logger.info(f"💥 Including {len(stress_tester.stress_scenarios)} historical crashes")
    logger.info(f"📈 With {500 * len(test_scenarios)} total simulations")
    
    return all_results, summary

if __name__ == "__main__":
    # Install additional dependencies
    try:
        import seaborn
    except ImportError:
        logger.info("Installing seaborn...")
        import subprocess
        subprocess.check_call(["pip3", "install", "seaborn"])
        
    # Run comprehensive stress testing
    results, summary = run_comprehensive_stress_testing()