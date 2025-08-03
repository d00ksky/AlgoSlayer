"""
Historical Backtesting Engine for AlgoSlayer
Simulates trading on historical data to generate massive training datasets
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sqlite3
import json
from loguru import logger
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

@dataclass
class HistoricalTrade:
    """Represents a simulated historical trade"""
    timestamp: datetime
    strategy: str
    symbol: str
    action: str
    option_type: str
    strike: float
    expiry: datetime
    entry_price: float
    entry_stock_price: float
    contracts: int
    confidence: float
    signals: Dict
    exit_price: Optional[float] = None
    exit_stock_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    exit_reason: Optional[str] = None
    
class HistoricalDataFetcher:
    """Fetches and caches historical data for backtesting"""
    
    def __init__(self, cache_dir: str = "historical_data_cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        import os
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def fetch_stock_history(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical stock data using yfinance"""
        cache_file = f"{self.cache_dir}/{symbol}_{start_date}_{end_date}_stock.csv"
        
        # Check cache first
        import os
        if os.path.exists(cache_file):
            logger.info(f"Loading {symbol} stock data from cache")
            return pd.read_csv(cache_file, index_col='Date', parse_dates=True)
        
        logger.info(f"Fetching {symbol} stock data from {start_date} to {end_date}")
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        
        # Add technical indicators
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['RSI'] = self._calculate_rsi(data['Close'])
        data['ATR'] = self._calculate_atr(data)
        
        # Save to cache
        data.to_csv(cache_file)
        return data
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def estimate_option_prices(self, stock_price: float, strike: float, 
                             days_to_expiry: int, volatility: float = 0.3) -> Dict:
        """Estimate option prices using simplified Black-Scholes approximation"""
        # Simplified option pricing for backtesting
        # In production, use real historical options data
        
        moneyness = stock_price / strike
        time_value = volatility * np.sqrt(days_to_expiry / 365) * stock_price * 0.4
        
        if moneyness > 1:  # ITM Call
            intrinsic = stock_price - strike
            call_price = intrinsic + time_value
            put_price = time_value * 0.3
        else:  # OTM Call
            intrinsic = 0
            call_price = time_value * moneyness
            put_price = (strike - stock_price) + time_value * 0.3 if strike > stock_price else time_value * 0.3
            
        return {
            'call': round(call_price, 2),
            'put': round(put_price, 2),
            'iv': volatility,
            'delta': 0.5 * moneyness if moneyness < 1.1 else 0.9,
            'gamma': 0.02,
            'theta': -time_value / days_to_expiry if days_to_expiry > 0 else 0
        }

class HistoricalSignalSimulator:
    """Simulates trading signals on historical data"""
    
    def __init__(self):
        self.signal_weights = {
            'technical_analysis': 0.15,
            'momentum': 0.12,
            'volatility': 0.10,
            'news_sentiment': 0.08,
            'options_flow': 0.11,
            'market_regime': 0.09,
            'sector_correlation': 0.08,
            'mean_reversion': 0.07,
            'iv_percentile': 0.14,
            'earnings': 0.06
        }
        
    def generate_signals(self, data: pd.DataFrame, current_date: datetime) -> Dict:
        """Generate trading signals based on historical data"""
        # Get recent data up to current_date
        recent_data = data[data.index <= current_date].tail(50)
        
        if len(recent_data) < 20:
            return {}
            
        current_price = recent_data['Close'].iloc[-1]
        
        signals = {}
        
        # Technical Analysis Signal
        sma_20 = recent_data['SMA_20'].iloc[-1]
        sma_50 = recent_data['SMA_50'].iloc[-1] if not pd.isna(recent_data['SMA_50'].iloc[-1]) else sma_20
        rsi = recent_data['RSI'].iloc[-1]
        
        technical_score = 0
        if current_price > sma_20:
            technical_score += 0.3
        if current_price > sma_50:
            technical_score += 0.3
        if 30 < rsi < 70:
            technical_score += 0.4
        elif rsi <= 30:
            technical_score += 0.6  # Oversold
        
        signals['technical_analysis'] = {
            'confidence': technical_score,
            'direction': 'bullish' if technical_score > 0.5 else 'bearish'
        }
        
        # Momentum Signal
        momentum_5d = (current_price - recent_data['Close'].iloc[-5]) / recent_data['Close'].iloc[-5]
        momentum_score = min(0.9, max(0.1, 0.5 + momentum_5d * 10))
        
        signals['momentum'] = {
            'confidence': momentum_score,
            'direction': 'bullish' if momentum_5d > 0 else 'bearish'
        }
        
        # Volatility Signal
        atr = recent_data['ATR'].iloc[-1]
        atr_pct = atr / current_price
        volatility_score = min(0.9, 0.3 + atr_pct * 20)
        
        signals['volatility'] = {
            'confidence': volatility_score,
            'direction': 'bullish' if recent_data['Volume'].iloc[-1] > recent_data['Volume'].mean() else 'neutral'
        }
        
        # Market Regime Signal (simplified)
        trend_strength = abs(sma_20 - sma_50) / current_price
        regime_score = min(0.9, 0.4 + trend_strength * 10)
        
        signals['market_regime'] = {
            'confidence': regime_score,
            'direction': 'trending' if trend_strength > 0.02 else 'ranging'
        }
        
        # Mean Reversion Signal
        deviation = (current_price - sma_20) / sma_20
        mean_reversion_score = min(0.9, abs(deviation) * 5)
        
        signals['mean_reversion'] = {
            'confidence': mean_reversion_score,
            'direction': 'bearish' if deviation > 0.03 else 'bullish' if deviation < -0.03 else 'neutral'
        }
        
        # Simplified signals for others
        signals['news_sentiment'] = {'confidence': 0.5, 'direction': 'neutral'}
        signals['options_flow'] = {'confidence': 0.5 + np.random.normal(0, 0.1), 'direction': 'bullish'}
        signals['sector_correlation'] = {'confidence': 0.5, 'direction': 'neutral'}
        signals['iv_percentile'] = {'confidence': 0.6, 'direction': 'bullish'}
        signals['earnings'] = {'confidence': 0.4, 'direction': 'neutral'}
        
        return signals
    
    def calculate_aggregate_confidence(self, signals: Dict) -> Tuple[float, str]:
        """Calculate weighted aggregate confidence from signals"""
        if not signals:
            return 0.0, 'neutral'
            
        total_confidence = 0
        total_weight = 0
        bullish_weight = 0
        
        for signal_name, signal_data in signals.items():
            if signal_name in self.signal_weights:
                weight = self.signal_weights[signal_name]
                confidence = signal_data.get('confidence', 0)
                direction = signal_data.get('direction', 'neutral')
                
                total_confidence += confidence * weight
                total_weight += weight
                
                if direction in ['bullish', 'trending']:
                    bullish_weight += weight
                    
        aggregate_confidence = total_confidence / total_weight if total_weight > 0 else 0
        aggregate_direction = 'bullish' if bullish_weight > total_weight * 0.5 else 'bearish'
        
        return aggregate_confidence, aggregate_direction

class HistoricalBacktestEngine:
    """Main backtesting engine that simulates trading strategies on historical data"""
    
    def __init__(self, data_fetcher: HistoricalDataFetcher, signal_simulator: HistoricalSignalSimulator):
        self.data_fetcher = data_fetcher
        self.signal_simulator = signal_simulator
        self.trades = []
        self.strategy_configs = {
            'conservative': {'min_confidence': 0.75, 'position_size': 0.1, 'max_days_to_expiry': 45},
            'moderate': {'min_confidence': 0.70, 'position_size': 0.15, 'max_days_to_expiry': 30},
            'aggressive': {'min_confidence': 0.65, 'position_size': 0.2, 'max_days_to_expiry': 14},
            'scalping': {'min_confidence': 0.60, 'position_size': 0.25, 'max_days_to_expiry': 7},
            'swing': {'min_confidence': 0.60, 'position_size': 0.15, 'max_days_to_expiry': 60},
            'momentum': {'min_confidence': 0.60, 'position_size': 0.15, 'max_days_to_expiry': 30},
            'volatility': {'min_confidence': 0.60, 'position_size': 0.2, 'max_days_to_expiry': 21},
            'mean_reversion': {'min_confidence': 0.60, 'position_size': 0.15, 'max_days_to_expiry': 30}
        }
        
    def backtest_period(self, symbol: str, start_date: str, end_date: str, 
                       initial_capital: float = 10000) -> pd.DataFrame:
        """Run backtest for a specific period"""
        logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
        
        # Fetch historical data
        stock_data = self.data_fetcher.fetch_stock_history(symbol, start_date, end_date)
        
        if stock_data.empty:
            logger.error("No historical data available")
            return pd.DataFrame()
        
        # Simulate trading for each day
        trading_days = stock_data.index[20:]  # Need 20 days of history for indicators
        
        all_trades = []
        
        for current_date in trading_days:
            # Generate signals for this day
            signals = self.signal_simulator.generate_signals(stock_data, current_date)
            
            if not signals:
                continue
                
            # Calculate aggregate confidence
            confidence, direction = self.signal_simulator.calculate_aggregate_confidence(signals)
            
            # Try each strategy
            for strategy_name, config in self.strategy_configs.items():
                if confidence >= config['min_confidence']:
                    # Generate a trade
                    trade = self._create_trade(
                        symbol, strategy_name, current_date, 
                        stock_data.loc[current_date], signals, 
                        confidence, direction, config
                    )
                    
                    if trade:
                        # Simulate trade exit
                        exit_trade = self._simulate_trade_exit(
                            trade, stock_data, current_date
                        )
                        all_trades.append(exit_trade)
        
        # Convert to DataFrame for analysis
        if all_trades:
            trades_df = pd.DataFrame([self._trade_to_dict(t) for t in all_trades])
            logger.info(f"Completed backtest: {len(all_trades)} trades generated")
            return trades_df
        else:
            logger.warning("No trades generated during backtest")
            return pd.DataFrame()
    
    def _create_trade(self, symbol: str, strategy: str, current_date: datetime,
                     current_data: pd.Series, signals: Dict, confidence: float,
                     direction: str, config: Dict) -> Optional[HistoricalTrade]:
        """Create a simulated trade"""
        current_price = current_data['Close']
        
        # Determine option parameters
        option_type = 'call' if direction == 'bullish' else 'put'
        
        # Strike selection (ATM to slightly OTM)
        if option_type == 'call':
            strike = round(current_price * 1.02)  # 2% OTM
        else:
            strike = round(current_price * 0.98)  # 2% OTM
            
        # Expiry selection
        days_to_expiry = min(30, config['max_days_to_expiry'])
        expiry = current_date + timedelta(days=days_to_expiry)
        
        # Estimate option price
        volatility = current_data.get('ATR', 0) / current_price if current_price > 0 else 0.3
        option_prices = self.data_fetcher.estimate_option_prices(
            current_price, strike, days_to_expiry, volatility
        )
        
        entry_price = option_prices[option_type]
        
        # Calculate position size
        capital_to_use = 10000 * config['position_size']  # Assume $10k account
        contracts = int(capital_to_use / (entry_price * 100))
        
        if contracts == 0:
            return None
            
        return HistoricalTrade(
            timestamp=current_date,
            strategy=strategy,
            symbol=symbol,
            action='BUY_TO_OPEN',
            option_type=option_type.upper(),
            strike=strike,
            expiry=expiry,
            entry_price=entry_price,
            entry_stock_price=current_price,
            contracts=contracts,
            confidence=confidence,
            signals=signals
        )
    
    def _simulate_trade_exit(self, trade: HistoricalTrade, 
                           stock_data: pd.DataFrame, 
                           entry_date: datetime) -> HistoricalTrade:
        """Simulate trade exit based on various conditions"""
        exit_date = None
        exit_reason = None
        
        # Check each day after entry
        future_dates = stock_data.index[stock_data.index > entry_date]
        
        for date in future_dates:
            if date > trade.expiry:
                exit_date = trade.expiry
                exit_reason = "expiry"
                break
                
            days_held = (date - entry_date).days
            current_price = stock_data.loc[date, 'Close']
            
            # Estimate current option price
            days_to_expiry = (trade.expiry - date).days
            volatility = stock_data.loc[date, 'ATR'] / current_price if current_price > 0 else 0.3
            
            option_prices = self.data_fetcher.estimate_option_prices(
                current_price, trade.strike, days_to_expiry, volatility
            )
            
            current_option_price = option_prices[trade.option_type.lower()]
            
            # Exit conditions
            pnl_pct = (current_option_price - trade.entry_price) / trade.entry_price
            
            # Take profit at 100%
            if pnl_pct >= 1.0:
                exit_date = date
                exit_reason = "take_profit_100%"
                break
                
            # Stop loss at -50%
            if pnl_pct <= -0.5:
                exit_date = date
                exit_reason = "stop_loss"
                break
                
            # Exit if held for strategy's typical duration
            strategy_typical_days = {
                'scalping': 1,
                'aggressive': 5,
                'moderate': 10,
                'conservative': 15,
                'swing': 20,
                'momentum': 10,
                'volatility': 7,
                'mean_reversion': 10
            }
            
            if days_held >= strategy_typical_days.get(trade.strategy, 10):
                exit_date = date
                exit_reason = "time_exit"
                break
        
        # If no exit triggered, exit at expiry
        if exit_date is None:
            exit_date = min(trade.expiry, stock_data.index[-1])
            exit_reason = "expiry" if exit_date == trade.expiry else "backtest_end"
            
        # Calculate final option price
        exit_price_data = stock_data.loc[exit_date] if exit_date in stock_data.index else stock_data.iloc[-1]
        exit_stock_price = exit_price_data['Close']
        
        days_to_expiry = max(0, (trade.expiry - exit_date).days)
        volatility = exit_price_data.get('ATR', 0) / exit_stock_price if exit_stock_price > 0 else 0.3
        
        option_prices = self.data_fetcher.estimate_option_prices(
            exit_stock_price, trade.strike, days_to_expiry, volatility
        )
        
        exit_option_price = option_prices[trade.option_type.lower()]
        
        # Handle expiry
        if exit_reason == "expiry":
            # Calculate intrinsic value at expiry
            if trade.option_type == 'CALL':
                exit_option_price = max(0, exit_stock_price - trade.strike)
            else:
                exit_option_price = max(0, trade.strike - exit_stock_price)
        
        # Update trade with exit info
        trade.exit_timestamp = exit_date
        trade.exit_price = exit_option_price
        trade.exit_stock_price = exit_stock_price
        trade.exit_reason = exit_reason
        
        # Calculate P&L
        trade.pnl = (exit_option_price - trade.entry_price) * trade.contracts * 100
        trade.pnl_percentage = ((exit_option_price - trade.entry_price) / trade.entry_price) * 100
        
        return trade
    
    def _trade_to_dict(self, trade: HistoricalTrade) -> Dict:
        """Convert trade object to dictionary for DataFrame"""
        return {
            'timestamp': trade.timestamp,
            'strategy': trade.strategy,
            'symbol': trade.symbol,
            'action': trade.action,
            'option_type': trade.option_type,
            'strike': trade.strike,
            'expiry': trade.expiry,
            'entry_price': trade.entry_price,
            'entry_stock_price': trade.entry_stock_price,
            'contracts': trade.contracts,
            'confidence': trade.confidence,
            'exit_timestamp': trade.exit_timestamp,
            'exit_price': trade.exit_price,
            'exit_stock_price': trade.exit_stock_price,
            'exit_reason': trade.exit_reason,
            'pnl': trade.pnl,
            'pnl_percentage': trade.pnl_percentage,
            'days_held': (trade.exit_timestamp - trade.timestamp).days if trade.exit_timestamp else 0,
            'signals': json.dumps(trade.signals)
        }
    
    def analyze_results(self, trades_df: pd.DataFrame) -> Dict:
        """Analyze backtest results"""
        if trades_df.empty:
            return {}
            
        analysis = {
            'total_trades': len(trades_df),
            'by_strategy': {},
            'overall_metrics': {}
        }
        
        # Overall metrics
        profitable_trades = trades_df[trades_df['pnl'] > 0]
        analysis['overall_metrics'] = {
            'win_rate': len(profitable_trades) / len(trades_df) * 100,
            'average_win': profitable_trades['pnl_percentage'].mean() if len(profitable_trades) > 0 else 0,
            'average_loss': trades_df[trades_df['pnl'] < 0]['pnl_percentage'].mean() if len(trades_df[trades_df['pnl'] < 0]) > 0 else 0,
            'total_pnl': trades_df['pnl'].sum(),
            'sharpe_ratio': self._calculate_sharpe_ratio(trades_df),
            'max_drawdown': self._calculate_max_drawdown(trades_df)
        }
        
        # By strategy analysis
        for strategy in trades_df['strategy'].unique():
            strategy_trades = trades_df[trades_df['strategy'] == strategy]
            profitable = strategy_trades[strategy_trades['pnl'] > 0]
            
            analysis['by_strategy'][strategy] = {
                'total_trades': len(strategy_trades),
                'win_rate': len(profitable) / len(strategy_trades) * 100 if len(strategy_trades) > 0 else 0,
                'total_pnl': strategy_trades['pnl'].sum(),
                'average_pnl_pct': strategy_trades['pnl_percentage'].mean(),
                'best_trade': strategy_trades['pnl_percentage'].max(),
                'worst_trade': strategy_trades['pnl_percentage'].min(),
                'avg_days_held': strategy_trades['days_held'].mean()
            }
            
        return analysis
    
    def _calculate_sharpe_ratio(self, trades_df: pd.DataFrame) -> float:
        """Calculate Sharpe ratio from trades"""
        if trades_df.empty:
            return 0
            
        # Group by date and calculate daily returns
        daily_pnl = trades_df.groupby(trades_df['timestamp'].dt.date)['pnl'].sum()
        
        if len(daily_pnl) < 2:
            return 0
            
        # Assume $10,000 starting capital
        daily_returns = daily_pnl / 10000
        
        # Annualized Sharpe ratio (252 trading days)
        if daily_returns.std() > 0:
            sharpe = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252))
            return sharpe
        return 0
    
    def _calculate_max_drawdown(self, trades_df: pd.DataFrame) -> float:
        """Calculate maximum drawdown from trades"""
        if trades_df.empty:
            return 0
            
        # Calculate cumulative P&L
        trades_df = trades_df.sort_values('timestamp')
        cumulative_pnl = trades_df['pnl'].cumsum()
        
        # Calculate running maximum
        running_max = cumulative_pnl.expanding().max()
        
        # Calculate drawdown
        drawdown = (cumulative_pnl - running_max) / 10000  # As percentage of initial capital
        
        return drawdown.min() * 100  # Return as percentage