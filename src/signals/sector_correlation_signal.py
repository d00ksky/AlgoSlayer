"""
Sector Correlation Analysis Signal
Analyze RTX performance vs defense sector and broader market
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger

from config.trading_config import config

class SectorCorrelationSignal:
    """Analyze RTX correlation with defense sector and market"""
    
    def __init__(self):
        self.signal_name = "sector_correlation"
        self.weight = config.SIGNAL_WEIGHTS.get(self.signal_name, 0.10)
        self.last_analysis = None
        
        # Defense sector tickers and market indices
        self.defense_tickers = ['LMT', 'NOC', 'GD', 'BA', 'TXT']  # Defense peers
        self.market_indices = ['SPY', 'QQQ', 'DIA']  # Market benchmarks
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze sector correlation for trading signals"""
        
        try:
            # Get price data for all tickers
            price_data = await self._get_correlation_data(symbol)
            
            if not price_data or symbol not in price_data:
                return self._create_neutral_signal("No correlation data available")
            
            # Calculate correlations
            correlation_analysis = self._calculate_correlations(price_data, symbol)
            
            # Analyze relative performance
            performance_analysis = self._analyze_relative_performance(price_data, symbol)
            
            # Generate signal
            signal = self._generate_signal(correlation_analysis, performance_analysis)
            
            self.last_analysis = signal
            return signal
            
        except Exception as e:
            logger.error(f"📊 Sector correlation error: {e}")
            return self._create_neutral_signal(f"Analysis error: {str(e)}")
    
    async def _get_correlation_data(self, symbol: str, period: str = "60d") -> Dict:
        """Get price data for RTX, defense sector, and market"""
        
        # All tickers to analyze
        all_tickers = [symbol] + self.defense_tickers + self.market_indices
        
        price_data = {}
        
        for ticker in all_tickers:
            try:
                yf_ticker = yf.Ticker(ticker)
                data = yf_ticker.history(period=period)
                
                if not data.empty:
                    # Calculate returns
                    data['Returns'] = data['Close'].pct_change()
                    price_data[ticker] = data
                    
            except Exception as e:
                logger.warning(f"📊 Failed to get data for {ticker}: {e}")
                continue
        
        logger.info(f"📊 Loaded correlation data for {len(price_data)} tickers")
        return price_data
    
    def _calculate_correlations(self, price_data: Dict, symbol: str) -> Dict:
        """Calculate correlation coefficients"""
        
        correlations = {
            'defense_sector': {},
            'market_indices': {},
            'average_defense_correlation': 0,
            'average_market_correlation': 0
        }
        
        if symbol not in price_data:
            return correlations
        
        rtx_returns = price_data[symbol]['Returns'].dropna()
        
        # Defense sector correlations
        defense_correlations = []
        for ticker in self.defense_tickers:
            if ticker in price_data:
                other_returns = price_data[ticker]['Returns'].dropna()
                
                # Align data
                common_dates = rtx_returns.index.intersection(other_returns.index)
                if len(common_dates) > 20:  # Need sufficient data
                    correlation = rtx_returns.loc[common_dates].corr(other_returns.loc[common_dates])
                    
                    if not np.isnan(correlation):
                        correlations['defense_sector'][ticker] = correlation
                        defense_correlations.append(correlation)
        
        # Market correlations
        market_correlations = []
        for ticker in self.market_indices:
            if ticker in price_data:
                other_returns = price_data[ticker]['Returns'].dropna()
                
                common_dates = rtx_returns.index.intersection(other_returns.index)
                if len(common_dates) > 20:
                    correlation = rtx_returns.loc[common_dates].corr(other_returns.loc[common_dates])
                    
                    if not np.isnan(correlation):
                        correlations['market_indices'][ticker] = correlation
                        market_correlations.append(correlation)
        
        # Calculate averages
        if defense_correlations:
            correlations['average_defense_correlation'] = np.mean(defense_correlations)
        
        if market_correlations:
            correlations['average_market_correlation'] = np.mean(market_correlations)
        
        return correlations
    
    def _analyze_relative_performance(self, price_data: Dict, symbol: str) -> Dict:
        """Analyze RTX performance relative to sector and market"""
        
        performance = {
            'rtx_performance': {},
            'defense_outperformance': {},
            'market_outperformance': {},
            'relative_strength': 'neutral'
        }
        
        if symbol not in price_data:
            return performance
        
        rtx_data = price_data[symbol]
        
        # Calculate RTX performance over different periods
        periods = [5, 10, 20]  # 5, 10, 20 days
        
        for period in periods:
            if len(rtx_data) > period:
                period_return = (rtx_data['Close'].iloc[-1] / rtx_data['Close'].iloc[-period-1] - 1) * 100
                performance['rtx_performance'][f'{period}d'] = period_return
        
        # Compare to defense sector
        for ticker in self.defense_tickers:
            if ticker in price_data:
                other_data = price_data[ticker]
                
                outperformance = {}
                for period in periods:
                    if len(other_data) > period and len(rtx_data) > period:
                        rtx_return = (rtx_data['Close'].iloc[-1] / rtx_data['Close'].iloc[-period-1] - 1) * 100
                        other_return = (other_data['Close'].iloc[-1] / other_data['Close'].iloc[-period-1] - 1) * 100
                        outperformance[f'{period}d'] = rtx_return - other_return
                
                performance['defense_outperformance'][ticker] = outperformance
        
        # Compare to market
        for ticker in self.market_indices:
            if ticker in price_data:
                other_data = price_data[ticker]
                
                outperformance = {}
                for period in periods:
                    if len(other_data) > period and len(rtx_data) > period:
                        rtx_return = (rtx_data['Close'].iloc[-1] / rtx_data['Close'].iloc[-period-1] - 1) * 100
                        other_return = (other_data['Close'].iloc[-1] / other_data['Close'].iloc[-period-1] - 1) * 100
                        outperformance[f'{period}d'] = rtx_return - other_return
                
                performance['market_outperformance'][ticker] = outperformance
        
        # Determine relative strength
        performance['relative_strength'] = self._calculate_relative_strength(performance)
        
        return performance
    
    def _calculate_relative_strength(self, performance: Dict) -> str:
        """Calculate overall relative strength"""
        
        # Collect all outperformance data
        all_outperformance = []
        
        # Defense outperformance
        for ticker_data in performance['defense_outperformance'].values():
            for period_perf in ticker_data.values():
                all_outperformance.append(period_perf)
        
        # Market outperformance
        for ticker_data in performance['market_outperformance'].values():
            for period_perf in ticker_data.values():
                all_outperformance.append(period_perf)
        
        if not all_outperformance:
            return 'neutral'
        
        # Calculate average outperformance
        avg_outperformance = np.mean(all_outperformance)
        
        if avg_outperformance > 1.0:  # >1% outperformance
            return 'strong'
        elif avg_outperformance > 0.2:  # >0.2% outperformance
            return 'positive'
        elif avg_outperformance < -1.0:  # <-1% underperformance
            return 'weak'
        elif avg_outperformance < -0.2:  # <-0.2% underperformance
            return 'negative'
        else:
            return 'neutral'
    
    def _generate_signal(self, correlations: Dict, performance: Dict) -> Dict:
        """Generate trading signal from correlation and performance analysis"""
        
        defense_correlation = correlations.get('average_defense_correlation', 0)
        market_correlation = correlations.get('average_market_correlation', 0)
        relative_strength = performance.get('relative_strength', 'neutral')
        
        # Signal logic
        direction = "HOLD"
        confidence = 0.5
        signal_strength = 0.1
        
        # Strong relative performance
        if relative_strength == 'strong':
            direction = "BUY"
            confidence = 0.70
        elif relative_strength == 'positive':
            direction = "BUY"
            confidence = 0.60
        elif relative_strength == 'weak':
            direction = "SELL"
            confidence = 0.65
        elif relative_strength == 'negative':
            direction = "SELL"
            confidence = 0.55
        
        # Correlation adjustments
        if defense_correlation > 0.8:  # Very high correlation
            confidence *= 0.9  # Slightly lower confidence (less alpha)
        elif defense_correlation < 0.3:  # Low correlation
            confidence *= 1.1  # Higher confidence (more independent)
        
        # Market correlation adjustments
        if market_correlation > 0.9:  # Very high market correlation
            confidence *= 0.85  # Lower confidence (market dependent)
        
        confidence = min(0.90, confidence)  # Cap confidence
        
        if direction != "HOLD":
            signal_strength = confidence * self.weight
        
        # Create reasoning
        reasoning = f"Sector analysis: {relative_strength} relative performance"
        if defense_correlation > 0:
            reasoning += f", defense correlation: {defense_correlation:.2f}"
        if market_correlation > 0:
            reasoning += f", market correlation: {market_correlation:.2f}"
        
        return {
            "signal_name": self.signal_name,
            "direction": direction,
            "strength": signal_strength,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "correlation_data": {
                "defense_correlation": defense_correlation,
                "market_correlation": market_correlation,
                "relative_strength": relative_strength,
                "defense_correlations": correlations.get('defense_sector', {}),
                "market_correlations": correlations.get('market_indices', {})
            }
        }
    
    def _create_neutral_signal(self, reason: str) -> Dict:
        """Create neutral signal with reason"""
        return {
            "signal_name": self.signal_name,
            "direction": "HOLD",
            "strength": 0.1,
            "confidence": 0.5,
            "reasoning": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_signal_status(self) -> Dict:
        """Get current signal status"""
        return {
            "signal_name": self.signal_name,
            "weight": self.weight,
            "last_analysis": self.last_analysis,
            "status": "operational",
            "tracked_tickers": {
                "defense_sector": self.defense_tickers,
                "market_indices": self.market_indices
            }
        } 