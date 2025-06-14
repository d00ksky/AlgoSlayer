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
        self.signals: List[BaseSignal] = []
        self.initialize_signals()
        logger.info(f"Signal Fusion Engine initialized with {len(self.signals)} signals")
    
    def initialize_signals(self):
        """Initialize all AI signals"""
        # Core signals
        self.signals.append(NewsSentimentSignal())
        self.signals.append(TechnicalAnalysisSignal())
        self.signals.append(OptionsFlowSignal())
        self.signals.append(VolatilityAnalysisSignal())
        self.signals.append(MomentumSignal())
        self.signals.append(SectorCorrelationSignal())
        self.signals.append(MeanReversionSignal())
        self.signals.append(MarketRegimeSignal())
        
        # NEW HIGH-VALUE OPTIONS SIGNALS
        self.signals.append(RTXEarningsSignal())
        self.signals.append(OptionsIVPercentileSignal())
        self.signals.append(DefenseContractSignal())
        self.signals.append(TrumpGeopoliticalSignal())
        
        logger.success(f"✅ Initialized {len(self.signals)} AI signals for options trading")
    
    async def get_all_signals(self, symbol: str) -> List[SignalResult]:
        """Gather signals from all enabled AI modules"""
        logger.info(f"Gathering signals for {symbol}")
        
        # Run all signal analyses in parallel for speed
        signal_tasks = [
            signal.get_signal_if_enabled(symbol) 
            for signal in self.signals
        ]
        
        # Wait for all signals to complete
        signal_results = await asyncio.gather(*signal_tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_signals = []
        for result in signal_results:
            if isinstance(result, SignalResult):
                valid_signals.append(result)
                logger.info(f"Signal {result.signal_name}: {result.direction} (confidence: {result.confidence:.2f})")
            elif isinstance(result, Exception):
                logger.error(f"Signal error: {result}")
        
        return valid_signals
    
    def calculate_fusion_confidence(self, signals: List[SignalResult]) -> float:
        """Calculate overall confidence from multiple signals"""
        if not signals:
            return 0.0
        
        # Weight signals by their individual confidence and configured weights
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for signal in signals:
            weight = config.SIGNAL_WEIGHTS.get(signal.signal_name, 0.1)
            total_weighted_confidence += signal.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return min(1.0, total_weighted_confidence / total_weight)
    
    def determine_consensus_action(self, signals: List[SignalResult]) -> tuple[str, str]:
        """Determine consensus action and trade type from signals"""
        if not signals:
            return "HOLD", None
        
        buy_signals = [s for s in signals if s.direction == "BUY"]
        sell_signals = [s for s in signals if s.direction == "SELL"]
        
        # Calculate weighted votes
        buy_weight = sum(s.confidence * config.SIGNAL_WEIGHTS.get(s.signal_name, 0.1) for s in buy_signals)
        sell_weight = sum(s.confidence * config.SIGNAL_WEIGHTS.get(s.signal_name, 0.1) for s in sell_signals)
        
        # Determine action
        if buy_weight > sell_weight and buy_weight > 0.3:
            # Determine trade type from buy signals
            call_signals = [s for s in buy_signals if s.trade_type == "CALL"]
            return "BUY", "CALL" if call_signals else "CALL"
        elif sell_weight > buy_weight and sell_weight > 0.3:
            # Determine trade type from sell signals  
            put_signals = [s for s in sell_signals if s.trade_type == "PUT"]
            return "SELL", "PUT" if put_signals else "PUT"
        else:
            return "HOLD", None
    
    def calculate_position_size(self, confidence: float, risk_score: float) -> float:
        """Calculate position size based on confidence and risk"""
        base_size = config.STARTING_CAPITAL * config.POSITION_SIZE_PCT
        
        # Adjust based on confidence
        confidence_multiplier = confidence
        
        # Adjust based on risk (lower risk = larger position)
        risk_multiplier = max(0.5, 1.0 - risk_score)
        
        # Apply maximum position size limit
        position_size = base_size * confidence_multiplier * risk_multiplier
        return min(position_size, config.MAX_POSITION_SIZE)
    
    def calculate_risk_score(self, signals: List[SignalResult]) -> float:
        """Calculate overall risk score (0.0 = low risk, 1.0 = high risk)"""
        if not signals:
            return 1.0  # High risk if no signals
        
        # Factor in signal agreement (more agreement = lower risk)
        directions = [s.direction for s in signals]
        unique_directions = set(directions)
        agreement_score = 1.0 - (len(unique_directions) - 1) / max(1, len(signals))
        
        # Factor in average confidence (higher confidence = lower risk)
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        confidence_score = avg_confidence
        
        # Combine factors (lower is better)
        risk_score = 1.0 - (agreement_score * 0.6 + confidence_score * 0.4)
        return max(0.0, min(1.0, risk_score))
    
    async def make_trading_decision(self, symbol: str) -> TradingDecision:
        """Main method: Fuse all signals and make trading decision"""
        decision = TradingDecision()
        decision.symbol = symbol
        
        # Gather all signals
        signals = await self.get_all_signals(symbol)
        decision.signals_used = signals
        
        # Check minimum signal requirement
        if len(signals) < config.MIN_SIGNALS_REQUIRED:
            decision.reasoning = f"Insufficient signals: {len(signals)} < {config.MIN_SIGNALS_REQUIRED} required"
            logger.warning(decision.reasoning)
            return decision
        
        # Calculate fusion metrics
        decision.confidence = self.calculate_fusion_confidence(signals)
        decision.risk_score = self.calculate_risk_score(signals)
        
        # Check confidence threshold
        if decision.confidence < config.CONFIDENCE_THRESHOLD:
            decision.reasoning = f"Low confidence: {decision.confidence:.2f} < {config.CONFIDENCE_THRESHOLD} threshold"
            logger.info(decision.reasoning)
            return decision
        
        # Determine action and trade type
        decision.action, decision.trade_type = self.determine_consensus_action(signals)
        
        # Calculate position size
        if decision.action != "HOLD":
            decision.position_size = self.calculate_position_size(decision.confidence, decision.risk_score)
        
        # Create reasoning summary
        signal_summary = ", ".join([
            f"{s.signal_name}:{s.direction}({s.confidence:.2f})" 
            for s in signals
        ])
        decision.reasoning = f"Fusion decision from {len(signals)} signals: {signal_summary}"
        
        logger.info(f"Trading Decision: {decision.action} {decision.trade_type} with confidence {decision.confidence:.2f}")
        
        return decision
    
    def add_signal(self, signal: BaseSignal):
        """Add a new signal to the fusion engine"""
        self.signals.append(signal)
        logger.info(f"Added signal: {signal.name}")
    
    def remove_signal(self, signal_name: str):
        """Remove a signal from the fusion engine"""
        self.signals = [s for s in self.signals if s.name != signal_name]
        logger.info(f"Removed signal: {signal_name}")
    
    def update_signal_weight(self, signal_name: str, new_weight: float):
        """Update weight for a specific signal"""
        for signal in self.signals:
            if signal.name == signal_name:
                signal.set_weight(new_weight)
                logger.info(f"Updated {signal_name} weight to {new_weight}")
                break 