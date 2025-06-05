"""
Defense Sector Momentum Analyzer
Analyzes RTX correlation with defense sector (ITA ETF) and peer stocks (LMT, NOC, GD)
Defense stocks move together 80% of the time - this provides predictive edge
"""
import asyncio
import logging
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SectorAnalysis:
    """Defense sector momentum analysis result"""
    rtx_correlation: float
    sector_momentum: float
    peer_divergence: float
    sector_strength: str  # 'strong_bullish', 'bullish', 'neutral', 'bearish', 'strong_bearish'
    prediction_confidence: float
    expected_rtx_move: float
    analysis_timestamp: datetime
    supporting_data: Dict[str, Any]

class DefenseSectorAnalyzer:
    """
    Analyzes RTX within defense sector context
    
    Key Insights:
    - Defense stocks move together during geopolitical events
    - ITA ETF correlation provides sector momentum
    - Peer analysis (LMT, NOC, GD) shows relative strength
    - Government contract announcements affect entire sector
    """
    
    def __init__(self):
        self.rtx_symbol = "RTX"
        self.sector_etf = "ITA"  # iShares U.S. Aerospace & Defense ETF
        self.peer_stocks = ["LMT", "NOC", "GD", "BA"]  # Lockheed, Northrop, General Dynamics, Boeing
        self.analysis_periods = [5, 10, 20, 50]  # Days for correlation analysis
        self.cache_duration = timedelta(hours=1)
        self.last_analysis = None
        self.cached_data = {}
        
    async def get_market_data(self, symbols: List[str], period: str = "3mo") -> Dict[str, pd.DataFrame]:
        """Fetch market data for analysis"""
        try:
            data = {}
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if not hist.empty:
                    data[symbol] = hist
                    logger.debug(f"Retrieved {len(hist)} days of data for {symbol}")
                else:
                    logger.warning(f"No data retrieved for {symbol}")
            return data
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {}
    
    def calculate_correlations(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Calculate RTX correlations with sector and peers"""
        correlations = {}
        
        if self.rtx_symbol not in data:
            logger.error("RTX data not available for correlation analysis")
            return correlations
        
        rtx_returns = data[self.rtx_symbol]['Close'].pct_change().dropna()
        
        for symbol, df in data.items():
            if symbol == self.rtx_symbol:
                continue
            
            try:
                symbol_returns = df['Close'].pct_change().dropna()
                # Align the data
                aligned_data = pd.concat([rtx_returns, symbol_returns], axis=1, join='inner').dropna()
                if len(aligned_data) > 10:  # Need sufficient data points
                    correlation = aligned_data.iloc[:, 0].corr(aligned_data.iloc[:, 1])
                    correlations[symbol] = correlation
                    logger.debug(f"RTX-{symbol} correlation: {correlation:.3f}")
            except Exception as e:
                logger.warning(f"Error calculating correlation for {symbol}: {e}")
        
        return correlations
    
    def analyze_sector_momentum(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Analyze overall sector momentum"""
        momentum_data = {}
        
        for symbol, df in data.items():
            try:
                # Calculate momentum indicators
                current_price = df['Close'].iloc[-1]
                
                # Short-term momentum (5-day)
                if len(df) >= 5:
                    price_5d_ago = df['Close'].iloc[-5]
                    momentum_5d = (current_price - price_5d_ago) / price_5d_ago
                else:
                    momentum_5d = 0
                
                # Medium-term momentum (20-day)
                if len(df) >= 20:
                    price_20d_ago = df['Close'].iloc[-20]
                    momentum_20d = (current_price - price_20d_ago) / price_20d_ago
                else:
                    momentum_20d = 0
                
                # Volatility (20-day)
                if len(df) >= 20:
                    returns_20d = df['Close'].pct_change().tail(20)
                    volatility = returns_20d.std() * np.sqrt(252)  # Annualized
                else:
                    volatility = 0
                
                momentum_data[symbol] = {
                    'momentum_5d': momentum_5d,
                    'momentum_20d': momentum_20d,
                    'volatility': volatility,
                    'current_price': current_price
                }
                
            except Exception as e:
                logger.warning(f"Error analyzing momentum for {symbol}: {e}")
        
        return momentum_data
    
    def detect_sector_divergence(self, momentum_data: Dict[str, Dict], correlations: Dict[str, float]) -> Dict[str, float]:
        """Detect when RTX diverges from sector - opportunity signal"""
        divergence_signals = {}
        
        if self.rtx_symbol not in momentum_data:
            return divergence_signals
        
        rtx_momentum_5d = momentum_data[self.rtx_symbol]['momentum_5d']
        rtx_momentum_20d = momentum_data[self.rtx_symbol]['momentum_20d']
        
        # Compare RTX momentum with sector ETF
        if self.sector_etf in momentum_data:
            eta_momentum_5d = momentum_data[self.sector_etf]['momentum_5d']
            eta_momentum_20d = momentum_data[self.sector_etf]['momentum_20d']
            
            divergence_5d = rtx_momentum_5d - eta_momentum_5d
            divergence_20d = rtx_momentum_20d - eta_momentum_20d
            
            divergence_signals['sector_divergence_5d'] = divergence_5d
            divergence_signals['sector_divergence_20d'] = divergence_20d
        
        # Compare RTX with peer average
        peer_momentum_5d = []
        peer_momentum_20d = []
        
        for peer in self.peer_stocks:
            if peer in momentum_data:
                peer_momentum_5d.append(momentum_data[peer]['momentum_5d'])
                peer_momentum_20d.append(momentum_data[peer]['momentum_20d'])
        
        if peer_momentum_5d:
            avg_peer_momentum_5d = np.mean(peer_momentum_5d)
            avg_peer_momentum_20d = np.mean(peer_momentum_20d)
            
            peer_divergence_5d = rtx_momentum_5d - avg_peer_momentum_5d
            peer_divergence_20d = rtx_momentum_20d - avg_peer_momentum_20d
            
            divergence_signals['peer_divergence_5d'] = peer_divergence_5d
            divergence_signals['peer_divergence_20d'] = peer_divergence_20d
        
        return divergence_signals
    
    def calculate_sector_strength(self, momentum_data: Dict[str, Dict], correlations: Dict[str, float]) -> Tuple[str, float]:
        """Calculate overall sector strength and confidence"""
        
        # Sector ETF momentum weight
        sector_momentum = 0
        sector_weight = 0.4
        
        if self.sector_etf in momentum_data:
            eta_momentum = momentum_data[self.sector_etf]['momentum_20d']
            sector_momentum = eta_momentum * sector_weight
        
        # Peer stocks momentum (average)
        peer_momentum = 0
        peer_weight = 0.6
        peer_momenta = []
        
        for peer in self.peer_stocks:
            if peer in momentum_data:
                peer_momenta.append(momentum_data[peer]['momentum_20d'])
        
        if peer_momenta:
            avg_peer_momentum = np.mean(peer_momenta)
            peer_momentum = avg_peer_momentum * peer_weight
        
        # Combined sector strength
        total_momentum = sector_momentum + peer_momentum
        
        # Determine strength category
        if total_momentum > 0.05:
            strength = "strong_bullish"
            confidence = min(0.9, 0.5 + abs(total_momentum) * 5)
        elif total_momentum > 0.02:
            strength = "bullish"
            confidence = min(0.8, 0.4 + abs(total_momentum) * 5)
        elif total_momentum > -0.02:
            strength = "neutral"
            confidence = 0.3
        elif total_momentum > -0.05:
            strength = "bearish"
            confidence = min(0.8, 0.4 + abs(total_momentum) * 5)
        else:
            strength = "strong_bearish"
            confidence = min(0.9, 0.5 + abs(total_momentum) * 5)
        
        return strength, confidence
    
    def predict_rtx_move(self, momentum_data: Dict[str, Dict], correlations: Dict[str, float], 
                        divergence_signals: Dict[str, float]) -> float:
        """Predict expected RTX move based on sector analysis"""
        
        if self.rtx_symbol not in momentum_data:
            return 0.0
        
        # Base expectation from sector momentum
        sector_momentum = 0
        if self.sector_etf in momentum_data and self.sector_etf in correlations:
            eta_momentum = momentum_data[self.sector_etf]['momentum_5d']
            eta_correlation = correlations[self.sector_etf]
            sector_momentum = eta_momentum * eta_correlation * 0.4
        
        # Peer influence
        peer_influence = 0
        for peer in self.peer_stocks:
            if peer in momentum_data and peer in correlations:
                peer_momentum = momentum_data[peer]['momentum_5d']
                peer_correlation = correlations[peer]
                peer_influence += peer_momentum * peer_correlation * (0.6 / len(self.peer_stocks))
        
        # Divergence mean reversion
        mean_reversion = 0
        if 'sector_divergence_5d' in divergence_signals:
            # If RTX diverged significantly, expect some mean reversion
            divergence = divergence_signals['sector_divergence_5d']
            if abs(divergence) > 0.02:  # 2% divergence threshold
                mean_reversion = -divergence * 0.3  # 30% reversion expectation
        
        # Combine predictions
        expected_move = sector_momentum + peer_influence + mean_reversion
        
        # Cap extreme predictions
        expected_move = np.clip(expected_move, -0.1, 0.1)  # Max ±10%
        
        return expected_move
    
    async def analyze_sector(self) -> Optional[SectorAnalysis]:
        """Main analysis method - provides comprehensive sector analysis"""
        try:
            # Check cache
            if (self.last_analysis and 
                datetime.now() - self.last_analysis < self.cache_duration and
                self.cached_data):
                logger.info("Using cached sector analysis")
                return self.cached_data
            
            logger.info("Starting defense sector analysis")
            
            # Get market data
            all_symbols = [self.rtx_symbol, self.sector_etf] + self.peer_stocks
            data = await self.get_market_data(all_symbols)
            
            if not data or self.rtx_symbol not in data:
                logger.error("Insufficient data for sector analysis")
                return None
            
            # Calculate correlations
            correlations = self.calculate_correlations(data)
            
            # Analyze momentum
            momentum_data = self.analyze_sector_momentum(data)
            
            # Detect divergences
            divergence_signals = self.detect_sector_divergence(momentum_data, correlations)
            
            # Calculate sector strength
            sector_strength, prediction_confidence = self.calculate_sector_strength(momentum_data, correlations)
            
            # Predict RTX move
            expected_rtx_move = self.predict_rtx_move(momentum_data, correlations, divergence_signals)
            
            # Get RTX correlation with sector ETF
            rtx_correlation = correlations.get(self.sector_etf, 0.0)
            
            # Calculate overall sector momentum
            sector_momentum = 0
            if self.sector_etf in momentum_data:
                sector_momentum = momentum_data[self.sector_etf]['momentum_20d']
            
            # Calculate peer divergence summary
            peer_divergence = divergence_signals.get('peer_divergence_5d', 0.0)
            
            # Create analysis result
            analysis = SectorAnalysis(
                rtx_correlation=rtx_correlation,
                sector_momentum=sector_momentum,
                peer_divergence=peer_divergence,
                sector_strength=sector_strength,
                prediction_confidence=prediction_confidence,
                expected_rtx_move=expected_rtx_move,
                analysis_timestamp=datetime.now(),
                supporting_data={
                    'correlations': correlations,
                    'momentum_data': momentum_data,
                    'divergence_signals': divergence_signals,
                    'data_symbols': list(data.keys())
                }
            )
            
            # Cache results
            self.cached_data = analysis
            self.last_analysis = datetime.now()
            
            logger.info(f"Sector analysis complete - Strength: {sector_strength}, "
                       f"RTX correlation: {rtx_correlation:.3f}, "
                       f"Expected move: {expected_rtx_move:.3f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in sector analysis: {e}")
            return None
    
    def get_trading_signal(self, analysis: SectorAnalysis) -> Dict[str, Any]:
        """Convert sector analysis to trading signal"""
        
        signal_strength = 0
        signal_direction = "neutral"
        confidence = analysis.prediction_confidence
        
        # Sector momentum signal
        if analysis.sector_strength in ["strong_bullish", "bullish"]:
            if analysis.expected_rtx_move > 0.02:  # Expect >2% move
                signal_strength = 0.7 if analysis.sector_strength == "strong_bullish" else 0.5
                signal_direction = "bullish"
        elif analysis.sector_strength in ["strong_bearish", "bearish"]:
            if analysis.expected_rtx_move < -0.02:  # Expect >2% move down
                signal_strength = 0.7 if analysis.sector_strength == "strong_bearish" else 0.5
                signal_direction = "bearish"
        
        # Divergence opportunities
        if abs(analysis.peer_divergence) > 0.03:  # 3% divergence
            if analysis.rtx_correlation > 0.6:  # High correlation means reversion likely
                divergence_signal = -analysis.peer_divergence * 0.5
                if abs(divergence_signal) > signal_strength:
                    signal_strength = abs(divergence_signal)
                    signal_direction = "bullish" if divergence_signal > 0 else "bearish"
        
        # Confidence adjustments
        confidence = min(confidence, 0.9)  # Cap at 90%
        if signal_strength < 0.3:
            confidence *= 0.5  # Lower confidence for weak signals
        
        return {
            'signal_strength': signal_strength,
            'signal_direction': signal_direction,
            'confidence': confidence,
            'expected_move': analysis.expected_rtx_move,
            'sector_strength': analysis.sector_strength,
            'rtx_correlation': analysis.rtx_correlation,
            'peer_divergence': analysis.peer_divergence,
            'reasoning': self._generate_reasoning(analysis)
        }
    
    def _generate_reasoning(self, analysis: SectorAnalysis) -> str:
        """Generate human-readable reasoning for the signal"""
        reasoning = []
        
        # Sector strength
        if analysis.sector_strength in ["strong_bullish", "bullish"]:
            reasoning.append(f"Defense sector showing {analysis.sector_strength} momentum")
        elif analysis.sector_strength in ["strong_bearish", "bearish"]:
            reasoning.append(f"Defense sector showing {analysis.sector_strength} momentum")
        else:
            reasoning.append("Defense sector neutral")
        
        # Correlation
        if analysis.rtx_correlation > 0.7:
            reasoning.append(f"RTX highly correlated with sector ({analysis.rtx_correlation:.2f})")
        elif analysis.rtx_correlation < 0.3:
            reasoning.append(f"RTX showing low sector correlation ({analysis.rtx_correlation:.2f})")
        
        # Divergence
        if abs(analysis.peer_divergence) > 0.03:
            direction = "outperforming" if analysis.peer_divergence > 0 else "underperforming"
            reasoning.append(f"RTX {direction} peers by {abs(analysis.peer_divergence)*100:.1f}%")
        
        # Expected move
        if abs(analysis.expected_rtx_move) > 0.02:
            direction = "upward" if analysis.expected_rtx_move > 0 else "downward"
            reasoning.append(f"Expecting {abs(analysis.expected_rtx_move)*100:.1f}% {direction} move")
        
        return "; ".join(reasoning) if reasoning else "Neutral sector conditions"

# Example usage
async def main():
    """Test the defense sector analyzer"""
    analyzer = DefenseSectorAnalyzer()
    
    analysis = await analyzer.analyze_sector()
    if analysis:
        signal = analyzer.get_trading_signal(analysis)
        
        print("=== Defense Sector Analysis ===")
        print(f"Sector Strength: {analysis.sector_strength}")
        print(f"RTX Correlation: {analysis.rtx_correlation:.3f}")
        print(f"Sector Momentum: {analysis.sector_momentum:.3f}")
        print(f"Peer Divergence: {analysis.peer_divergence:.3f}")
        print(f"Expected RTX Move: {analysis.expected_rtx_move:.3f}")
        print(f"Confidence: {analysis.prediction_confidence:.3f}")
        
        print("\n=== Trading Signal ===")
        print(f"Direction: {signal['signal_direction']}")
        print(f"Strength: {signal['signal_strength']:.3f}")
        print(f"Confidence: {signal['confidence']:.3f}")
        print(f"Reasoning: {signal['reasoning']}")
    else:
        print("Failed to analyze sector")

if __name__ == "__main__":
    asyncio.run(main())