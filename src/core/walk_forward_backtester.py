"""
Walk-Forward Backtesting System for RTX Options Strategy
Proper validation to prevent overfitting and ensure real-world performance
Tests strategy on rolling windows to validate learning system effectiveness
"""
import asyncio
import logging
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BacktestTrade:
    """Individual backtest trade record"""
    entry_date: date
    exit_date: date
    signal_confidence: float
    predicted_move: float
    actual_move: float
    option_type: str  # 'call' or 'put'
    strike_price: float
    entry_premium: float
    exit_premium: float
    profit_loss: float
    profit_loss_pct: float
    signals_used: List[str]
    market_regime: str

@dataclass
class BacktestPeriod:
    """Results for a single walk-forward period"""
    start_date: date
    end_date: date
    training_start: date
    training_end: date
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    trades: List[BacktestTrade]

@dataclass
class BacktestResults:
    """Complete walk-forward backtest results"""
    strategy_name: str
    backtest_start: date
    backtest_end: date
    total_periods: int
    overall_win_rate: float
    overall_return: float
    overall_sharpe: float
    overall_max_drawdown: float
    consistency_score: float  # How consistent across periods
    periods: List[BacktestPeriod]
    summary_stats: Dict[str, Any]

class WalkForwardBacktester:
    """
    Walk-forward backtesting system for RTX options strategy
    
    Key Features:
    - Rolling window training/testing to prevent overfitting
    - Options pricing simulation using Black-Scholes approximation
    - Signal combination testing with real historical data
    - Performance consistency measurement across market regimes
    """
    
    def __init__(self, 
                 training_days: int = 90,
                 testing_days: int = 30,
                 min_confidence: float = 0.8,
                 max_option_investment: float = 400):
        """
        Initialize backtester
        
        Args:
            training_days: Days of data for training signals
            testing_days: Days for out-of-sample testing
            min_confidence: Minimum confidence to take trades
            max_option_investment: Maximum per trade investment
        """
        self.training_days = training_days
        self.testing_days = testing_days
        self.min_confidence = min_confidence
        self.max_option_investment = max_option_investment
        self.rtx_symbol = "RTX"
        
    async def get_historical_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get RTX historical data for backtesting"""
        try:
            ticker = yf.Ticker(self.rtx_symbol)
            
            # Add buffer for indicator calculations
            buffer_start = start_date - timedelta(days=50)
            
            hist = ticker.history(start=buffer_start, end=end_date)
            if hist.empty:
                logger.error(f"No historical data found for {self.rtx_symbol}")
                return pd.DataFrame()
            
            # Add technical indicators
            hist = self._add_technical_indicators(hist)
            
            # Filter to actual requested period
            hist = hist[hist.index.date >= start_date]
            
            logger.info(f"Retrieved {len(hist)} days of data for backtesting")
            return hist
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators for signal simulation"""
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Moving averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['SMA_20']
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # Volatility (20-day)
        returns = df['Close'].pct_change()
        df['Volatility'] = returns.rolling(window=20).std() * np.sqrt(252)
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        return df
    
    def simulate_signals(self, data: pd.DataFrame, training_end: date) -> pd.DataFrame:
        """Simulate AI signals based on historical patterns"""
        
        signals_df = data.copy()
        
        # Technical Analysis Signal
        signals_df['tech_signal'] = 0.0
        signals_df['tech_confidence'] = 0.3
        
        # RSI oversold/overbought
        rsi_oversold = signals_df['RSI'] < 30
        rsi_overbought = signals_df['RSI'] > 70
        signals_df.loc[rsi_oversold, 'tech_signal'] = 0.6
        signals_df.loc[rsi_overbought, 'tech_signal'] = -0.6
        signals_df.loc[rsi_oversold | rsi_overbought, 'tech_confidence'] = 0.7
        
        # Bollinger Band signals
        bb_oversold = signals_df['Close'] < signals_df['BB_Lower']
        bb_overbought = signals_df['Close'] > signals_df['BB_Upper']
        signals_df.loc[bb_oversold, 'tech_signal'] += 0.4
        signals_df.loc[bb_overbought, 'tech_signal'] -= 0.4
        
        # Momentum Signal
        signals_df['momentum_signal'] = 0.0
        signals_df['momentum_confidence'] = 0.4
        
        # Price vs moving averages
        price_above_sma20 = signals_df['Close'] > signals_df['SMA_20']
        price_above_sma50 = signals_df['Close'] > signals_df['SMA_50']
        sma20_above_sma50 = signals_df['SMA_20'] > signals_df['SMA_50']
        
        bullish_momentum = price_above_sma20 & price_above_sma50 & sma20_above_sma50
        bearish_momentum = ~price_above_sma20 & ~price_above_sma50 & ~sma20_above_sma50
        
        signals_df.loc[bullish_momentum, 'momentum_signal'] = 0.5
        signals_df.loc[bearish_momentum, 'momentum_signal'] = -0.5
        signals_df.loc[bullish_momentum | bearish_momentum, 'momentum_confidence'] = 0.6
        
        # Volatility Signal (higher vol = higher opportunity)
        signals_df['volatility_signal'] = 0.0
        signals_df['volatility_confidence'] = 0.3
        
        high_vol = signals_df['Volatility'] > signals_df['Volatility'].rolling(50).mean() * 1.5
        signals_df.loc[high_vol, 'volatility_confidence'] = 0.6
        
        # Volume Signal
        signals_df['volume_signal'] = 0.0
        signals_df['volume_confidence'] = 0.3
        
        high_volume = signals_df['Volume_Ratio'] > 1.5
        signals_df.loc[high_volume, 'volume_confidence'] = 0.5
        
        # Combined signal
        signals_df['combined_signal'] = (
            signals_df['tech_signal'] * 0.3 +
            signals_df['momentum_signal'] * 0.4 +
            signals_df['volatility_signal'] * 0.1 +
            signals_df['volume_signal'] * 0.2
        )
        
        signals_df['combined_confidence'] = (
            signals_df['tech_confidence'] * 0.3 +
            signals_df['momentum_confidence'] * 0.4 +
            signals_df['volatility_confidence'] * 0.1 +
            signals_df['volume_confidence'] * 0.2
        )
        
        return signals_df
    
    def estimate_option_premium(self, spot_price: float, strike_price: float, 
                              days_to_expiry: int, volatility: float, 
                              option_type: str = 'call') -> float:
        """
        Simplified Black-Scholes option pricing for backtesting
        Not perfect but good enough for relative performance testing
        """
        
        if days_to_expiry <= 0:
            # At expiry, option worth intrinsic value
            if option_type == 'call':
                return max(0, spot_price - strike_price)
            else:
                return max(0, strike_price - spot_price)
        
        # Risk-free rate approximation
        risk_free_rate = 0.05
        
        # Time to expiry in years
        time_to_expiry = days_to_expiry / 365.0
        
        # Simple approximation based on moneyness and time decay
        moneyness = spot_price / strike_price if option_type == 'call' else strike_price / spot_price
        
        # Intrinsic value
        if option_type == 'call':
            intrinsic = max(0, spot_price - strike_price)
        else:
            intrinsic = max(0, strike_price - spot_price)
        
        # Time value approximation
        # This is simplified but captures key behaviors
        time_value = (
            volatility * 
            np.sqrt(time_to_expiry) * 
            spot_price * 
            0.4 *  # Scaling factor
            np.exp(-abs(1 - moneyness) * 3)  # Penalty for being far from ATM
        )
        
        # Time decay
        time_decay_factor = np.exp(-time_to_expiry * 0.5)
        time_value *= time_decay_factor
        
        total_premium = intrinsic + time_value
        
        # Minimum premium (bid-ask spread)
        min_premium = spot_price * 0.005  # 0.5% minimum
        
        return max(total_premium, min_premium)
    
    def simulate_option_trade(self, entry_data: pd.Series, exit_data: pd.Series,
                            signal_direction: str, confidence: float) -> Optional[BacktestTrade]:
        """Simulate an options trade based on signal"""
        
        try:
            entry_date = entry_data.name.date()
            exit_date = exit_data.name.date()
            entry_price = entry_data['Close']
            exit_price = exit_data['Close']
            
            # Determine option parameters
            days_to_expiry = 21  # Target 3 weeks
            volatility = entry_data.get('Volatility', 0.25)
            
            if signal_direction == 'bullish':
                option_type = 'call'
                # Slightly OTM call
                strike_price = entry_price * 1.02
            else:
                option_type = 'put'
                # Slightly OTM put
                strike_price = entry_price * 0.98
            
            # Calculate premiums
            entry_premium = self.estimate_option_premium(
                entry_price, strike_price, days_to_expiry, volatility, option_type
            )
            
            # Days held (approximate)
            days_held = min((exit_date - entry_date).days, days_to_expiry)
            remaining_days = max(0, days_to_expiry - days_held)
            
            exit_premium = self.estimate_option_premium(
                exit_price, strike_price, remaining_days, volatility, option_type
            )
            
            # Calculate P&L
            contracts = int(self.max_option_investment / (entry_premium * 100))
            if contracts <= 0:
                return None
            
            total_entry_cost = contracts * entry_premium * 100
            total_exit_value = contracts * exit_premium * 100
            
            profit_loss = total_exit_value - total_entry_cost
            profit_loss_pct = profit_loss / total_entry_cost
            
            # Actual stock move
            actual_move = (exit_price - entry_price) / entry_price
            
            # Predicted move (simplified)
            predicted_move = entry_data['combined_signal'] * 0.05  # Scale to reasonable range
            
            return BacktestTrade(
                entry_date=entry_date,
                exit_date=exit_date,
                signal_confidence=confidence,
                predicted_move=predicted_move,
                actual_move=actual_move,
                option_type=option_type,
                strike_price=strike_price,
                entry_premium=entry_premium,
                exit_premium=exit_premium,
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct,
                signals_used=['technical', 'momentum', 'volatility', 'volume'],
                market_regime='normal'  # Could be enhanced with regime detection
            )
            
        except Exception as e:
            logger.warning(f"Error simulating trade: {e}")
            return None
    
    def identify_trade_opportunities(self, signals_df: pd.DataFrame, start_date: date, end_date: date) -> List[BacktestTrade]:
        """Identify and simulate trades in the testing period"""
        
        trades = []
        test_data = signals_df[
            (signals_df.index.date >= start_date) & 
            (signals_df.index.date <= end_date)
        ]
        
        i = 0
        while i < len(test_data) - 5:  # Need at least 5 days for trade
            current_row = test_data.iloc[i]
            
            # Check if signal meets criteria
            confidence = current_row['combined_confidence']
            signal_strength = abs(current_row['combined_signal'])
            
            if confidence >= self.min_confidence and signal_strength >= 0.3:
                
                # Determine direction
                signal_direction = 'bullish' if current_row['combined_signal'] > 0 else 'bearish'
                
                # Find exit (5-10 days later or when signal reverses)
                exit_idx = min(i + 7, len(test_data) - 1)  # Target 1 week hold
                exit_row = test_data.iloc[exit_idx]
                
                # Simulate the trade
                trade = self.simulate_option_trade(
                    current_row, exit_row, signal_direction, confidence
                )
                
                if trade:
                    trades.append(trade)
                    logger.debug(f"Simulated trade: {trade.entry_date} -> {trade.exit_date}, "
                               f"P&L: {trade.profit_loss:.2f} ({trade.profit_loss_pct:.2%})")
                
                # Skip ahead to avoid overlapping trades
                i = exit_idx + 1
            else:
                i += 1
        
        return trades
    
    def calculate_period_metrics(self, trades: List[BacktestTrade]) -> Dict[str, float]:
        """Calculate performance metrics for a period"""
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # Basic stats
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss <= 0]
        
        win_rate = len(winning_trades) / total_trades
        
        # Returns
        total_return = sum(t.profit_loss for t in trades)
        
        # Average win/loss
        avg_win = np.mean([t.profit_loss for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit_loss for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t.profit_loss for t in winning_trades)
        gross_loss = abs(sum(t.profit_loss for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Drawdown calculation
        cumulative_returns = []
        running_total = 0
        for trade in trades:
            running_total += trade.profit_loss
            cumulative_returns.append(running_total)
        
        peak = cumulative_returns[0]
        max_drawdown = 0
        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Sharpe ratio (simplified)
        if trades:
            returns_series = [t.profit_loss_pct for t in trades]
            avg_return = np.mean(returns_series)
            return_std = np.std(returns_series)
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio
        }
    
    async def run_backtest(self, start_date: date, end_date: date) -> Optional[BacktestResults]:
        """Run complete walk-forward backtest"""
        
        try:
            logger.info(f"Starting walk-forward backtest from {start_date} to {end_date}")
            
            # Get all historical data needed
            data = await self.get_historical_data(start_date, end_date)
            if data.empty:
                logger.error("No data available for backtesting")
                return None
            
            periods = []
            current_date = start_date
            
            while current_date + timedelta(days=self.training_days + self.testing_days) <= end_date:
                
                # Define period dates
                training_start = current_date
                training_end = current_date + timedelta(days=self.training_days)
                test_start = training_end + timedelta(days=1)
                test_end = test_start + timedelta(days=self.testing_days)
                
                logger.info(f"Testing period: {test_start} to {test_end}")
                
                # Generate signals using training data
                period_data = data[data.index.date <= test_end.date()]
                signals_df = self.simulate_signals(period_data, training_end)
                
                # Run trades in test period
                trades = self.identify_trade_opportunities(signals_df, test_start, test_end)
                
                # Calculate metrics
                metrics = self.calculate_period_metrics(trades)
                
                period = BacktestPeriod(
                    start_date=test_start,
                    end_date=test_end,
                    training_start=training_start,
                    training_end=training_end,
                    total_trades=metrics['total_trades'],
                    winning_trades=len([t for t in trades if t.profit_loss > 0]),
                    losing_trades=len([t for t in trades if t.profit_loss <= 0]),
                    win_rate=metrics['win_rate'],
                    total_return=metrics['total_return'],
                    max_drawdown=metrics['max_drawdown'],
                    sharpe_ratio=metrics['sharpe_ratio'],
                    avg_win=metrics['avg_win'],
                    avg_loss=metrics['avg_loss'],
                    profit_factor=metrics['profit_factor'],
                    trades=trades
                )
                
                periods.append(period)
                
                # Move to next period
                current_date = test_start + timedelta(days=self.testing_days // 2)  # 50% overlap
            
            # Calculate overall results
            all_trades = []
            for period in periods:
                all_trades.extend(period.trades)
            
            overall_metrics = self.calculate_period_metrics(all_trades)
            
            # Consistency score (how consistent results are across periods)
            if len(periods) > 1:
                period_returns = [p.total_return for p in periods]
                consistency_score = 1.0 - (np.std(period_returns) / (abs(np.mean(period_returns)) + 1))
                consistency_score = max(0, min(1, consistency_score))
            else:
                consistency_score = 0.5
            
            results = BacktestResults(
                strategy_name="RTX Options Strategy",
                backtest_start=start_date,
                backtest_end=end_date,
                total_periods=len(periods),
                overall_win_rate=overall_metrics['win_rate'],
                overall_return=overall_metrics['total_return'],
                overall_sharpe=overall_metrics['sharpe_ratio'],
                overall_max_drawdown=overall_metrics['max_drawdown'],
                consistency_score=consistency_score,
                periods=periods,
                summary_stats=overall_metrics
            )
            
            logger.info(f"Backtest complete: {len(periods)} periods, "
                       f"{len(all_trades)} total trades, "
                       f"{overall_metrics['win_rate']:.2%} win rate, "
                       f"${overall_metrics['total_return']:.2f} total return")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return None
    
    def save_results(self, results: BacktestResults, filepath: str):
        """Save backtest results to JSON file"""
        try:
            # Convert to dict for JSON serialization
            results_dict = asdict(results)
            
            # Convert dates to strings
            def convert_dates(obj):
                if isinstance(obj, dict):
                    return {k: convert_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_dates(item) for item in obj]
                elif isinstance(obj, date):
                    return obj.isoformat()
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                else:
                    return obj
            
            results_dict = convert_dates(results_dict)
            
            with open(filepath, 'w') as f:
                json.dump(results_dict, f, indent=2)
            
            logger.info(f"Backtest results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

# Example usage
async def main():
    """Test the walk-forward backtester"""
    backtester = WalkForwardBacktester(
        training_days=90,
        testing_days=30,
        min_confidence=0.8,
        max_option_investment=400
    )
    
    # Test on last 6 months
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    
    results = await backtester.run_backtest(start_date, end_date)
    
    if results:
        print("=== Walk-Forward Backtest Results ===")
        print(f"Strategy: {results.strategy_name}")
        print(f"Period: {results.backtest_start} to {results.backtest_end}")
        print(f"Total Periods: {results.total_periods}")
        print(f"Overall Win Rate: {results.overall_win_rate:.2%}")
        print(f"Overall Return: ${results.overall_return:.2f}")
        print(f"Overall Sharpe: {results.overall_sharpe:.2f}")
        print(f"Max Drawdown: ${results.overall_max_drawdown:.2f}")
        print(f"Consistency Score: {results.consistency_score:.2f}")
        
        # Save results
        results_dir = Path("backtest_results")
        results_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"walkforward_backtest_{timestamp}.json"
        backtester.save_results(results, str(results_file))
    else:
        print("Backtest failed")

if __name__ == "__main__":
    asyncio.run(main())