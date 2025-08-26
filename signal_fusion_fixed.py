"""
Signal Fusion Engine
Combines multiple AI signals for high-confidence trading decisions
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from src.signals.base_signal import BaseSignal, SignalResult
from src.signals.news_sentiment_signal import NewsSentimentSignal
from src.signals.technical_analysis_signal import TechnicalAnalysisSignal
from src.signals.options_flow_signal import OptionsFlowSignal
from src.signals.volatility_analysis_signal import VolatilityAnalysisSignal
from src.signals.momentum_signal import MomentumSignal
from src.signals.sector_correlation_signal import SectorCorrelationSignal
from src.signals.mean_reversion_signal import MeanReversionSignal
from src.signals.market_regime_signal import MarketRegimeSignal
# NEW HIGH-VALUE SIGNALS
from src.signals.rtx_earnings_signal import RTXEarningsSignal
from src.signals.options_iv_percentile_signal import OptionsIVPercentileSignal
from src.signals.defense_contract_signal import DefenseContractSignal
from src.signals.trump_geopolitical_signal import TrumpGeopoliticalSignal
from config.trading_config import config

class TradingDecision:
    """Final trading decision from signal fusion"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.symbol: str = ""
        self.action: str = "HOLD"  # BUY, SELL, HOLD
        self.confidence: float = 0.0
        self.trade_type: Optional[str] = None  # CALL, PUT
        self.position_size: float = 0.0
        self.signals_used: List[SignalResult] = []
        self.reasoning: str = ""
        self.risk_score: float = 0.0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "trade_type": self.trade_type,
            "position_size": self.position_size,
            "signals_count": len(self.signals_used),
            "reasoning": self.reasoning,
            "risk_score": self.risk_score
        }

class SignalFusionEngine:
    """Multi-AI Signal Fusion for RTX Trading"""
    
    def __init__(self):
        self.signals = []
        self.initialize_signals()
        logger.info(f"Signal Fusion Engine initialized with {len(self.signals)} signals")
    
    def initialize_signals(self):
        """Initialize all AI signals - mixed BaseSignal and legacy signals"""
        # Initialize signals (some BaseSignal, some legacy)
        signal_classes = [
            NewsSentimentSignal,
            TechnicalAnalysisSignal,
            OptionsFlowSignal,
            VolatilityAnalysisSignal,
            MomentumSignal,
            SectorCorrelationSignal,
            MeanReversionSignal,
            MarketRegimeSignal,
            RTXEarningsSignal,
            OptionsIVPercentileSignal,
            DefenseContractSignal,
            TrumpGeopoliticalSignal
        ]
        
        for signal_class in signal_classes:
            try:
                signal = signal_class()
                self.signals.append(signal)
                logger.info(f"✅ Initialized {signal_class.__name__}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {signal_class.__name__}: {e}")
        
        logger.success(f"✅ Initialized {len(self.signals)} AI signals for options trading")
    
    async def get_signal_safely(self, signal, symbol: str):
        """Get signal from either BaseSignal or legacy signal"""
        try:
            # Try BaseSignal method first
            if hasattr(signal, 'get_signal_if_enabled'):
                result = await signal.get_signal_if_enabled(symbol)
                if result is not None:
                    return result
            
            # Fallback to legacy analyze() method
            if hasattr(signal, 'analyze'):
                raw_result = await signal.analyze(symbol)
                
                # Convert dict result to SignalResult if needed
                if isinstance(raw_result, dict):
                    signal_name = getattr(signal, 'signal_name', signal.__class__.__name__.lower().replace('signal', ''))
                    
                    return SignalResult(
                        signal_name=signal_name,
                        timestamp=datetime.now(),
                        confidence=raw_result.get('confidence', 50) / 100.0,  # Convert to 0-1
                        direction=raw_result.get('direction', 'HOLD'),
                        reasoning=raw_result.get('reasoning', f'Analysis from {signal_name}'),
                        trade_type=raw_result.get('trade_type'),
                        expiry_suggestion=raw_result.get('expiry_suggestion'),
                        strike_suggestion=raw_result.get('strike_suggestion')
                    )
                elif hasattr(raw_result, 'confidence'):
                    # Already a SignalResult
                    return raw_result
            
            logger.warning(f"Signal {signal.__class__.__name__} has no compatible method")
            return None
            
        except Exception as e:
            logger.error(f"Error getting signal from {signal.__class__.__name__}: {e}")
            return None
    
    async def get_all_signals(self, symbol: str) -> List[SignalResult]:
        """Gather signals from all AI modules - works with both BaseSignal and legacy signals"""
        logger.info(f"Gathering signals for {symbol}")
        
        # Run all signal analyses in parallel for speed
        signal_tasks = [
            self.get_signal_safely(signal, symbol) 
            for signal in self.signals
        ]
        
        # Wait for all signals to complete
        signal_results = await asyncio.gather(*signal_tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_signals = []
        for i, result in enumerate(signal_results):
            if isinstance(result, SignalResult):
                valid_signals.append(result)
                logger.info(f"✅ Signal {result.signal_name}: {result.direction} (confidence: {result.confidence:.2f})")
            elif isinstance(result, Exception):
                logger.error(f"❌ Signal {i} exception: {result}")
            elif result is None:
                logger.warning(f"⚠️  Signal {i} returned None")
        
        logger.info(f"Collected {len(valid_signals)}/{len(self.signals)} valid signals")
        return valid_signals
    
    def analyze_signal_consensus(self, signals: List[SignalResult]) -> Dict[str, Any]:
        """Analyze consensus among signals"""
        if not signals:
            return {
                "consensus_direction": "HOLD",
                "average_confidence": 0.0,
                "signals_agreeing": 0,
                "total_signals": 0,
                "consensus_strength": 0.0
            }
        
        # Count directions
        direction_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
        total_confidence = 0.0
        
        for signal in signals:
            direction_counts[signal.direction] += 1
            total_confidence += signal.confidence
        
        # Determine consensus
        max_direction = max(direction_counts, key=direction_counts.get)
        signals_agreeing = direction_counts[max_direction]
        
        return {
            "consensus_direction": max_direction,
            "average_confidence": total_confidence / len(signals),
            "signals_agreeing": signals_agreeing,
            "total_signals": len(signals),
            "consensus_strength": signals_agreeing / len(signals),
            "direction_breakdown": direction_counts
        }
    
    async def make_trading_decision(self, symbol: str = "RTX") -> TradingDecision:
        """Make final trading decision based on signal fusion"""
        decision = TradingDecision()
        decision.symbol = symbol
        
        try:
            # Get all signals
            signals = await self.get_all_signals(symbol)
            decision.signals_used = signals
            
            if not signals:
                decision.reasoning = "No valid signals received"
                logger.warning("❌ No valid signals for trading decision")
                return decision
            
            # Analyze consensus
            consensus = self.analyze_signal_consensus(signals)
            
            # Apply decision logic
            decision.action = consensus["consensus_direction"]
            decision.confidence = consensus["average_confidence"]
            
            # Generate reasoning
            decision.reasoning = f"Consensus: {consensus['signals_agreeing']}/{consensus['total_signals']} signals agree on {decision.action} (avg confidence: {decision.confidence:.1%})"
            
            logger.info(f"🎯 Trading Decision: {decision.action} with {decision.confidence:.1%} confidence ({consensus['signals_agreeing']}/{consensus['total_signals']} signals)")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error making trading decision: {e}")
            decision.reasoning = f"Error in decision making: {str(e)}"
            return decision

# Global instance
signal_fusion_engine = SignalFusionEngine()
