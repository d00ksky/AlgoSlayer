"""
RTX-Focused Signal Orchestrator
Integrates all 8 AI signals specifically for RTX Corporation stock trading
High-conviction strategy that only trades when multiple signals align
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import yfinance as yf
import numpy as np
import pandas as pd

from src.core.lightweight_ml import ml_system, MLPrediction
from src.core.signal_performance_tracker import SignalPerformanceTracker
from src.core.defense_sector_analyzer import DefenseSectorAnalyzer
from src.core.market_regime_detector import MarketRegimeDetector
from src.core.rtx_earnings_calendar import RTXEarningsCalendar
from src.signals.news_sentiment_signal import NewsSentimentSignal
from src.signals.technical_analysis_signal import TechnicalAnalysisSignal
from src.signals.options_flow_signal import OptionsFlowSignal
from src.signals.volatility_analysis_signal import VolatilityAnalysisSignal
from src.signals.momentum_signal import MomentumSignal
from src.signals.sector_correlation_signal import SectorCorrelationSignal
from src.signals.mean_reversion_signal import MeanReversionSignal
from src.signals.market_regime_signal import MarketRegimeSignal

@dataclass
class RTXSignalResult:
    timestamp: datetime
    signal_name: str
    direction: str  # BUY, SELL, HOLD
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    expected_move: float  # Expected % move
    rationale: str
    weight: float  # Signal weight in final decision

@dataclass
class RTXTradingDecision:
    timestamp: datetime
    action: str  # BUY, SELL, HOLD
    confidence: float  # Combined confidence
    expected_move: float  # Expected % move
    signals_agreeing: int  # Number of signals agreeing
    total_signals: int
    individual_signals: List[RTXSignalResult]
    ml_prediction: MLPrediction
    trade_worthy: bool  # High conviction trade?
    rationale: str
    # Enhanced learning data
    sector_analysis: Optional[dict] = field(default=None)
    market_regime: Optional[dict] = field(default=None)
    earnings_context: Optional[dict] = field(default=None)
    signal_performance_weights: Optional[dict] = field(default=None)

class RTXSignalOrchestrator:
    """
    Orchestrates all RTX-focused trading signals
    Only recommends trades when high conviction (3+ signals agree, 80%+ confidence)
    """
    
    def __init__(self):
        self.symbol = "RTX"
        self.logger = logging.getLogger(__name__)
        
        # Initialize all signals
        self.signals = {
            'news_sentiment': NewsSentimentSignal(),
            'technical_analysis': TechnicalAnalysisSignal(),
            'options_flow': OptionsFlowSignal(),
            'volatility_analysis': VolatilityAnalysisSignal(),
            'momentum': MomentumSignal(),
            'sector_correlation': SectorCorrelationSignal(),
            'mean_reversion': MeanReversionSignal(),
            'market_regime': MarketRegimeSignal()
        }
        
        # Enhanced learning components
        self.performance_tracker = SignalPerformanceTracker()
        self.sector_analyzer = DefenseSectorAnalyzer()
        self.regime_detector = MarketRegimeDetector()
        self.earnings_calendar = RTXEarningsCalendar()
        
        # Base signal weights (will be dynamically adjusted by performance tracker)
        self.base_signal_weights = {
            'news_sentiment': 0.15,      # 15% - RTX defense news is important
            'technical_analysis': 0.15,   # 15% - Classic TA
            'options_flow': 0.15,        # 15% - Options activity
            'volatility_analysis': 0.12,  # 12% - Vol patterns
            'momentum': 0.12,            # 12% - Multi-timeframe momentum
            'sector_correlation': 0.10,   # 10% - Defense sector moves
            'mean_reversion': 0.10,      # 10% - RTX stable, mean-reverting
            'market_regime': 0.11        # 11% - Market context
        }
        
        # Current weights (updated by learning system)
        self.signal_weights = self.base_signal_weights.copy()
        
        # High conviction thresholds (can be adjusted by market regime)
        self.base_min_signals_agreeing = 3  # Need 3+ signals to agree
        self.base_min_confidence = 0.80     # Need 80%+ confidence
        self.base_min_expected_move = 0.03  # Need 3%+ expected move
        
        # Current thresholds (adjusted by learning system)
        self.min_signals_agreeing = self.base_min_signals_agreeing
        self.min_confidence = self.base_min_confidence
        self.min_expected_move = self.base_min_expected_move
        
        # Historical performance tracking
        self.prediction_history = []
        self.last_analysis = None
        
    async def analyze_rtx(self) -> RTXTradingDecision:
        """
        Enhanced main analysis function with learning components
        """
        try:
            self.logger.info(f"🎯 Starting enhanced RTX analysis at {datetime.now()}")
            
            # Get current market data
            rtx_data = await self._get_rtx_data()
            if rtx_data.empty:
                return self._create_hold_decision("No market data available")
            
            # Run enhanced analysis components in parallel
            analysis_tasks = [
                asyncio.create_task(self._run_signal_analysis(rtx_data)),
                asyncio.create_task(self._run_sector_analysis()),
                asyncio.create_task(self._run_regime_analysis()),
                asyncio.create_task(self._run_earnings_analysis()),
                asyncio.create_task(self._update_signal_weights())
            ]
            
            # Wait for all analyses
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            valid_signals, sector_analysis, regime_analysis, earnings_context, updated_weights = results
            
            # Handle any failed analyses
            if isinstance(valid_signals, Exception):
                self.logger.warning(f"Signal analysis failed: {valid_signals}")
                valid_signals = []
            if isinstance(sector_analysis, Exception):
                self.logger.warning(f"Sector analysis failed: {sector_analysis}")
                sector_analysis = None
            if isinstance(regime_analysis, Exception):
                self.logger.warning(f"Regime analysis failed: {regime_analysis}")
                regime_analysis = None
            if isinstance(earnings_context, Exception):
                self.logger.warning(f"Earnings analysis failed: {earnings_context}")
                earnings_context = None
            if isinstance(updated_weights, Exception):
                self.logger.warning(f"Weight update failed: {updated_weights}")
                updated_weights = None
            
            # Get ML prediction
            ml_prediction = await self._get_ml_prediction(rtx_data)
            
            # Apply regime-based adjustments to thresholds
            self._adjust_thresholds_for_regime(regime_analysis)
            
            # Combine all signals into trading decision
            decision = await self._make_enhanced_trading_decision(
                valid_signals, ml_prediction, sector_analysis, 
                regime_analysis, earnings_context, updated_weights
            )
            
            # Track performance for learning
            await self._track_prediction_performance(decision)
            
            # Store for performance tracking
            self.last_analysis = decision
            self.prediction_history.append(decision)
            
            # Log enhanced decision
            self._log_enhanced_decision(decision)
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in enhanced RTX analysis: {e}")
            return self._create_hold_decision(f"Analysis error: {e}")
    
    async def _get_rtx_data(self) -> pd.DataFrame:
        """Get recent RTX market data"""
        try:
            ticker = yf.Ticker(self.symbol)
            # Get 5 days of hourly data for analysis
            data = ticker.history(period="5d", interval="1h")
            return data
        except Exception as e:
            self.logger.error(f"Error getting RTX data: {e}")
            return pd.DataFrame()
    
    async def _analyze_signal(self, name: str, signal, rtx_data: pd.DataFrame) -> RTXSignalResult:
        """Analyze individual signal"""
        try:
            # Each signal analyzes RTX specifically
            result = await signal.analyze(self.symbol, rtx_data)
            
            return RTXSignalResult(
                timestamp=datetime.now(),
                signal_name=name,
                direction=result.get('direction', 'HOLD'),
                strength=result.get('strength', 0.5),
                confidence=result.get('confidence', 0.5),
                expected_move=result.get('expected_move', 0.0),
                rationale=result.get('rationale', 'No details provided'),
                weight=self.signal_weights[name]
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing {name} signal: {e}")
            return RTXSignalResult(
                timestamp=datetime.now(),
                signal_name=name,
                direction='HOLD',
                strength=0.0,
                confidence=0.0,
                expected_move=0.0,
                rationale=f'Signal error: {e}',
                weight=self.signal_weights[name]
            )
    
    async def _get_ml_prediction(self, rtx_data: pd.DataFrame) -> MLPrediction:
        """Get ML system prediction"""
        try:
            # Prepare features from RTX data
            features = await ml_system.prepare_features(self.symbol, lookback_days=10)
            
            if features.empty:
                return MLPrediction(
                    timestamp=datetime.now(),
                    symbol=self.symbol,
                    direction="HOLD",
                    confidence=0.5,
                    expected_move=0.0,
                    features_used=[],
                    model_name="no_data"
                )
            
            # Make prediction
            prediction = await ml_system.predict(features)
            return prediction
            
        except Exception as e:
            self.logger.error(f"Error getting ML prediction: {e}")
            return MLPrediction(
                timestamp=datetime.now(),
                symbol=self.symbol,
                direction="HOLD",
                confidence=0.5,
                expected_move=0.0,
                features_used=[],
                model_name="error"
            )
    
    async def _make_trading_decision(self, signals: List[RTXSignalResult], ml_prediction: MLPrediction) -> RTXTradingDecision:
        """
        Combine all signals and ML to make final trading decision
        High conviction strategy - only trade when multiple signals agree
        """
        try:
            if not signals:
                return self._create_hold_decision("No valid signals")
            
            # Count signal directions
            buy_signals = [s for s in signals if s.direction == 'BUY']
            sell_signals = [s for s in signals if s.direction == 'SELL']
            hold_signals = [s for s in signals if s.direction == 'HOLD']
            
            # Calculate weighted vote
            buy_weight = sum(s.weight * s.confidence for s in buy_signals)
            sell_weight = sum(s.weight * s.confidence for s in sell_signals)
            hold_weight = sum(s.weight * s.confidence for s in hold_signals)
            
            # Determine primary direction
            if buy_weight > sell_weight and buy_weight > hold_weight:
                primary_direction = 'BUY'
                agreeing_signals = len(buy_signals)
                combined_confidence = buy_weight / sum(s.weight for s in buy_signals) if buy_signals else 0
                expected_move = np.mean([abs(s.expected_move) for s in buy_signals]) if buy_signals else 0
            elif sell_weight > buy_weight and sell_weight > hold_weight:
                primary_direction = 'SELL'
                agreeing_signals = len(sell_signals)
                combined_confidence = sell_weight / sum(s.weight for s in sell_signals) if sell_signals else 0
                expected_move = -np.mean([abs(s.expected_move) for s in sell_signals]) if sell_signals else 0
            else:
                primary_direction = 'HOLD'
                agreeing_signals = len(hold_signals)
                combined_confidence = 0.5
                expected_move = 0.0
            
            # Factor in ML prediction
            ml_weight = 0.2  # ML gets 20% vote
            if ml_prediction.direction == primary_direction:
                combined_confidence = combined_confidence * 0.8 + ml_prediction.confidence * ml_weight
                if primary_direction != 'HOLD':
                    expected_move = expected_move * 0.8 + ml_prediction.expected_move * ml_weight
            else:
                # ML disagrees - reduce confidence
                combined_confidence *= 0.7
            
            # Determine if this is a high conviction trade
            trade_worthy = (
                agreeing_signals >= self.min_signals_agreeing and
                combined_confidence >= self.min_confidence and
                abs(expected_move) >= self.min_expected_move and
                primary_direction != 'HOLD'
            )
            
            # Build rationale
            rationale = self._build_rationale(
                primary_direction, agreeing_signals, len(signals), 
                combined_confidence, expected_move, ml_prediction
            )
            
            return RTXTradingDecision(
                timestamp=datetime.now(),
                action=primary_direction,
                confidence=combined_confidence,
                expected_move=expected_move,
                signals_agreeing=agreeing_signals,
                total_signals=len(signals),
                individual_signals=signals,
                ml_prediction=ml_prediction,
                trade_worthy=trade_worthy,
                rationale=rationale
            )
            
        except Exception as e:
            self.logger.error(f"Error making trading decision: {e}")
            return self._create_hold_decision(f"Decision error: {e}")
    
    def _build_rationale(self, direction: str, agreeing: int, total: int, 
                        confidence: float, expected_move: float, ml_pred: MLPrediction) -> str:
        """Build human-readable rationale for the decision"""
        
        rationale_parts = []
        
        # Signal agreement
        rationale_parts.append(f"{agreeing}/{total} signals agree on {direction}")
        
        # Confidence level
        if confidence >= 0.8:
            rationale_parts.append(f"High confidence ({confidence:.1%})")
        elif confidence >= 0.6:
            rationale_parts.append(f"Medium confidence ({confidence:.1%})")
        else:
            rationale_parts.append(f"Low confidence ({confidence:.1%})")
        
        # Expected move
        if abs(expected_move) >= 0.05:
            rationale_parts.append(f"Large expected move ({expected_move:+.1%})")
        elif abs(expected_move) >= 0.03:
            rationale_parts.append(f"Significant expected move ({expected_move:+.1%})")
        elif abs(expected_move) >= 0.01:
            rationale_parts.append(f"Small expected move ({expected_move:+.1%})")
        
        # ML agreement
        if ml_pred.direction == direction:
            rationale_parts.append(f"ML agrees ({ml_pred.confidence:.1%})")
        else:
            rationale_parts.append(f"ML disagrees ({ml_pred.direction}, {ml_pred.confidence:.1%})")
        
        return "; ".join(rationale_parts)
    
    def _create_hold_decision(self, reason: str) -> RTXTradingDecision:
        """Create a HOLD decision with given reason"""
        return RTXTradingDecision(
            timestamp=datetime.now(),
            action='HOLD',
            confidence=0.5,
            expected_move=0.0,
            signals_agreeing=0,
            total_signals=0,
            individual_signals=[],
            ml_prediction=MLPrediction(
                timestamp=datetime.now(),
                symbol=self.symbol,
                direction="HOLD",
                confidence=0.5,
                expected_move=0.0,
                features_used=[],
                model_name="default"
            ),
            trade_worthy=False,
            rationale=reason
        )
    
    def _log_decision(self, decision: RTXTradingDecision):
        """Log the trading decision"""
        self.logger.info(f"🎯 RTX TRADING DECISION")
        self.logger.info(f"   Action: {decision.action}")
        self.logger.info(f"   Confidence: {decision.confidence:.1%}")
        self.logger.info(f"   Expected Move: {decision.expected_move:+.1%}")
        self.logger.info(f"   Signals Agreeing: {decision.signals_agreeing}/{decision.total_signals}")
        self.logger.info(f"   Trade Worthy: {'YES' if decision.trade_worthy else 'NO'}")
        self.logger.info(f"   Rationale: {decision.rationale}")
        
        if decision.trade_worthy:
            self.logger.info(f"🚀 HIGH CONVICTION TRADE OPPORTUNITY!")
        
        # Log individual signals
        for signal in decision.individual_signals:
            self.logger.debug(f"   {signal.signal_name}: {signal.direction} "
                            f"({signal.confidence:.1%}, {signal.expected_move:+.1%})")
    
    # Enhanced analysis methods
    async def _run_signal_analysis(self, rtx_data: pd.DataFrame) -> List[RTXSignalResult]:
        """Run all signal analyses in parallel"""
        signal_tasks = []
        for name, signal in self.signals.items():
            task = asyncio.create_task(self._analyze_signal(name, signal, rtx_data))
            signal_tasks.append(task)
        
        signal_results = await asyncio.gather(*signal_tasks, return_exceptions=True)
        
        valid_signals = []
        for result in signal_results:
            if isinstance(result, RTXSignalResult):
                valid_signals.append(result)
            else:
                self.logger.warning(f"Signal failed: {result}")
        
        return valid_signals
    
    async def _run_sector_analysis(self) -> Optional[dict]:
        """Run defense sector analysis"""
        try:
            analysis = await self.sector_analyzer.analyze_sector()
            if analysis:
                signal = self.sector_analyzer.get_trading_signal(analysis)
                return {
                    'sector_strength': analysis.sector_strength,
                    'rtx_correlation': analysis.rtx_correlation,
                    'expected_move': analysis.expected_rtx_move,
                    'confidence': analysis.prediction_confidence,
                    'signal': signal
                }
            return None
        except Exception as e:
            self.logger.warning(f"Sector analysis error: {e}")
            return None
    
    async def _run_regime_analysis(self) -> Optional[dict]:
        """Run market regime analysis"""
        try:
            analysis = await self.regime_detector.detect_regime(self.symbol)
            if analysis:
                return {
                    'regime': analysis.current_regime.value,
                    'regime_strength': analysis.regime_strength,
                    'volatility_regime': analysis.volatility_regime.value,
                    'trend_direction': analysis.trend_direction,
                    'confidence': analysis.confidence,
                    'optimal_strategy': analysis.optimal_strategy,
                    'change_probability': analysis.regime_change_probability
                }
            return None
        except Exception as e:
            self.logger.warning(f"Regime analysis error: {e}")
            return None
    
    async def _run_earnings_analysis(self) -> Optional[dict]:
        """Run earnings calendar analysis"""
        try:
            analysis = await self.earnings_calendar.get_earnings_impact()
            if analysis:
                return {
                    'days_to_earnings': analysis.days_until_earnings,
                    'quarter': analysis.quarter,
                    'year': analysis.year,
                    'volatility_expectation': analysis.volatility_multiplier,
                    'confidence_boost': analysis.confidence_boost,
                    'historical_move_avg': analysis.historical_move_avg,
                    'recommendation': analysis.recommendation
                }
            return None
        except Exception as e:
            self.logger.warning(f"Earnings analysis error: {e}")
            return None
    
    async def _update_signal_weights(self) -> Optional[dict]:
        """Update signal weights based on performance"""
        try:
            # Get performance-adjusted weights
            performance_weights = await self.performance_tracker.get_adaptive_weights()
            
            if performance_weights:
                # Blend with base weights (70% performance, 30% base)
                updated_weights = {}
                for signal_name in self.base_signal_weights:
                    base_weight = self.base_signal_weights[signal_name]
                    perf_weight = performance_weights.get(signal_name, base_weight)
                    updated_weights[signal_name] = 0.7 * perf_weight + 0.3 * base_weight
                
                # Normalize to sum to 1.0
                total_weight = sum(updated_weights.values())
                if total_weight > 0:
                    updated_weights = {k: v/total_weight for k, v in updated_weights.items()}
                    self.signal_weights = updated_weights
                    return updated_weights
            
            return None
        except Exception as e:
            self.logger.warning(f"Weight update error: {e}")
            return None
    
    def _adjust_thresholds_for_regime(self, regime_analysis: Optional[dict]):
        """Adjust trading thresholds based on market regime"""
        if not regime_analysis:
            return
        
        regime = regime_analysis.get('regime', 'sideways')
        volatility_regime = regime_analysis.get('volatility_regime', 'sideways')
        
        # Reset to base thresholds
        self.min_signals_agreeing = self.base_min_signals_agreeing
        self.min_confidence = self.base_min_confidence
        self.min_expected_move = self.base_min_expected_move
        
        # Adjust based on regime
        if regime in ['strong_bull', 'strong_bear']:
            # Strong trending markets: lower thresholds (momentum works)
            self.min_signals_agreeing = max(2, self.base_min_signals_agreeing - 1)
            self.min_confidence = max(0.7, self.base_min_confidence - 0.1)
        elif regime == 'sideways':
            # Sideways markets: higher thresholds (harder to predict)
            self.min_signals_agreeing = self.base_min_signals_agreeing + 1
            self.min_confidence = min(0.9, self.base_min_confidence + 0.1)
        
        # Adjust for volatility
        if volatility_regime == 'high_volatility':
            # High vol: bigger moves possible, lower move threshold
            self.min_expected_move = max(0.02, self.base_min_expected_move - 0.01)
        elif volatility_regime == 'low_volatility':
            # Low vol: need bigger expected moves to justify options
            self.min_expected_move = min(0.05, self.base_min_expected_move + 0.01)
    
    async def _make_enhanced_trading_decision(self, signals: List[RTXSignalResult], 
                                           ml_prediction: MLPrediction,
                                           sector_analysis: Optional[dict],
                                           regime_analysis: Optional[dict],
                                           earnings_context: Optional[dict],
                                           updated_weights: Optional[dict]) -> RTXTradingDecision:
        """Enhanced trading decision with learning components"""
        try:
            # Start with base decision
            base_decision = await self._make_trading_decision(signals, ml_prediction)
            
            # Apply sector analysis adjustments
            if sector_analysis:
                sector_signal = sector_analysis.get('signal', {})
                if sector_signal.get('signal_direction') == base_decision.action:
                    # Sector agrees - boost confidence
                    boost = sector_signal.get('confidence', 0) * 0.2
                    base_decision.confidence = min(1.0, base_decision.confidence + boost)
                elif sector_signal.get('signal_direction') != 'neutral':
                    # Sector disagrees - reduce confidence
                    base_decision.confidence *= 0.8
            
            # Apply earnings context
            if earnings_context:
                days_to_earnings = earnings_context.get('days_to_earnings', 100)
                if 0 < days_to_earnings <= 14:  # Within 2 weeks of earnings
                    # Increase expected move and confidence for options
                    vol_boost = earnings_context.get('volatility_expectation', 1.0)
                    base_decision.expected_move *= vol_boost
                    base_decision.confidence = min(1.0, base_decision.confidence * 1.1)
            
            # Apply regime-specific adjustments
            if regime_analysis:
                regime = regime_analysis.get('regime', 'sideways')
                if regime in ['strong_bull', 'strong_bear']:
                    # Strong trends: boost momentum signals
                    momentum_signals = [s for s in signals if 'momentum' in s.signal_name.lower()]
                    if momentum_signals and base_decision.action != 'HOLD':
                        base_decision.confidence = min(1.0, base_decision.confidence * 1.1)
                
                optimal_strategy = regime_analysis.get('optimal_strategy', '')
                if 'Buy calls' in optimal_strategy and base_decision.action == 'BUY':
                    base_decision.confidence = min(1.0, base_decision.confidence * 1.15)
                elif 'Buy puts' in optimal_strategy and base_decision.action == 'SELL':
                    base_decision.confidence = min(1.0, base_decision.confidence * 1.15)
                elif 'Wait for' in optimal_strategy:
                    base_decision.confidence *= 0.7  # Reduce confidence when regime says wait
            
            # Re-check trade worthiness with updated confidence
            base_decision.trade_worthy = (
                base_decision.signals_agreeing >= self.min_signals_agreeing and
                base_decision.confidence >= self.min_confidence and
                abs(base_decision.expected_move) >= self.min_expected_move and
                base_decision.action != 'HOLD'
            )
            
            # Add enhanced data to decision
            base_decision.sector_analysis = sector_analysis
            base_decision.market_regime = regime_analysis
            base_decision.earnings_context = earnings_context
            base_decision.signal_performance_weights = updated_weights
            
            # Update rationale with enhanced info
            enhanced_rationale = self._build_enhanced_rationale(
                base_decision, sector_analysis, regime_analysis, earnings_context
            )
            base_decision.rationale = enhanced_rationale
            
            return base_decision
            
        except Exception as e:
            self.logger.error(f"Error in enhanced decision making: {e}")
            return await self._make_trading_decision(signals, ml_prediction)
    
    def _build_enhanced_rationale(self, decision: RTXTradingDecision,
                                sector_analysis: Optional[dict],
                                regime_analysis: Optional[dict],
                                earnings_context: Optional[dict]) -> str:
        """Build enhanced rationale including learning components"""
        rationale_parts = [decision.rationale]  # Start with base rationale
        
        # Add sector analysis
        if sector_analysis:
            sector_strength = sector_analysis.get('sector_strength', 'neutral')
            rtx_correlation = sector_analysis.get('rtx_correlation', 0)
            rationale_parts.append(f"Defense sector: {sector_strength} (RTX correlation: {rtx_correlation:.2f})")
        
        # Add regime analysis
        if regime_analysis:
            regime = regime_analysis.get('regime', 'unknown')
            vol_regime = regime_analysis.get('volatility_regime', 'unknown')
            rationale_parts.append(f"Market regime: {regime} / {vol_regime}")
        
        # Add earnings context
        if earnings_context:
            days_to_earnings = earnings_context.get('days_to_earnings', 100)
            if 0 < days_to_earnings <= 21:
                rationale_parts.append(f"Earnings in {days_to_earnings} days")
        
        return "; ".join(rationale_parts)
    
    async def _track_prediction_performance(self, decision: RTXTradingDecision):
        """Track prediction for performance learning"""
        try:
            # Record the prediction
            prediction_data = {
                'timestamp': decision.timestamp,
                'action': decision.action,
                'confidence': decision.confidence,
                'expected_move': decision.expected_move,
                'signals': {s.signal_name: {'direction': s.direction, 'confidence': s.confidence, 'strength': s.strength} 
                          for s in decision.individual_signals},
                'trade_worthy': decision.trade_worthy
            }
            
            await self.performance_tracker.record_prediction(
                self.symbol, prediction_data
            )
            
        except Exception as e:
            self.logger.warning(f"Error tracking performance: {e}")
    
    def _log_enhanced_decision(self, decision: RTXTradingDecision):
        """Log enhanced trading decision with learning data"""
        self._log_decision(decision)  # Base logging
        
        # Add enhanced logging
        if decision.sector_analysis:
            sector = decision.sector_analysis
            self.logger.info(f"🏭 Sector Analysis: {sector.get('sector_strength', 'unknown')} "
                           f"(correlation: {sector.get('rtx_correlation', 0):.2f})")
        
        if decision.market_regime:
            regime = decision.market_regime
            self.logger.info(f"📈 Market Regime: {regime.get('regime', 'unknown')} / "
                           f"{regime.get('volatility_regime', 'unknown')} "
                           f"(confidence: {regime.get('confidence', 0):.2f})")
        
        if decision.earnings_context:
            earnings = decision.earnings_context
            days_to = earnings.get('days_to_earnings', 100)
            if 0 < days_to <= 30:
                self.logger.info(f"📊 Earnings Context: {days_to} days to earnings "
                               f"(opportunity: {earnings.get('opportunity_score', 0):.2f})")
        
        if decision.signal_performance_weights:
            self.logger.debug(f"⚖️ Updated signal weights based on performance")
    
    def _create_hold_decision(self, reason: str) -> RTXTradingDecision:
        """Create enhanced HOLD decision with given reason"""
        return RTXTradingDecision(
            timestamp=datetime.now(),
            action='HOLD',
            confidence=0.5,
            expected_move=0.0,
            signals_agreeing=0,
            total_signals=0,
            individual_signals=[],
            ml_prediction=MLPrediction(
                timestamp=datetime.now(),
                symbol=self.symbol,
                direction="HOLD",
                confidence=0.5,
                expected_move=0.0,
                features_used=[],
                model_name="default"
            ),
            trade_worthy=False,
            rationale=reason,
            sector_analysis=None,
            market_regime=None,
            earnings_context=None,
            signal_performance_weights=None
        )
    
    async def get_performance_summary(self) -> Dict:
        """Get performance summary of predictions"""
        if not self.prediction_history:
            return {"total_predictions": 0, "message": "No predictions yet"}
        
        recent_predictions = self.prediction_history[-50:]  # Last 50 predictions
        
        trade_worthy_count = sum(1 for p in recent_predictions if p.trade_worthy)
        buy_count = sum(1 for p in recent_predictions if p.action == 'BUY')
        sell_count = sum(1 for p in recent_predictions if p.action == 'SELL')
        hold_count = sum(1 for p in recent_predictions if p.action == 'HOLD')
        
        avg_confidence = np.mean([p.confidence for p in recent_predictions])
        avg_signals_agreeing = np.mean([p.signals_agreeing for p in recent_predictions])
        
        return {
            "total_predictions": len(self.prediction_history),
            "recent_predictions": len(recent_predictions),
            "trade_worthy_opportunities": trade_worthy_count,
            "action_breakdown": {
                "BUY": buy_count,
                "SELL": sell_count,
                "HOLD": hold_count
            },
            "average_confidence": avg_confidence,
            "average_signals_agreeing": avg_signals_agreeing,
            "last_prediction": self.last_analysis.timestamp.isoformat() if self.last_analysis else None
        }

# Global orchestrator instance
rtx_orchestrator = RTXSignalOrchestrator()

async def test_rtx_orchestrator():
    """Test the RTX signal orchestrator"""
    print("🎯 Testing RTX Signal Orchestrator")
    print("=" * 50)
    
    try:
        decision = await rtx_orchestrator.analyze_rtx()
        
        print(f"📊 Analysis Result:")
        print(f"   Action: {decision.action}")
        print(f"   Confidence: {decision.confidence:.1%}")
        print(f"   Expected Move: {decision.expected_move:+.1%}")
        print(f"   Signals Agreeing: {decision.signals_agreeing}/{decision.total_signals}")
        print(f"   Trade Worthy: {'YES' if decision.trade_worthy else 'NO'}")
        print(f"   Rationale: {decision.rationale}")
        
        if decision.individual_signals:
            print(f"\n📈 Individual Signals:")
            for signal in decision.individual_signals:
                print(f"   {signal.signal_name}: {signal.direction} "
                      f"({signal.confidence:.1%}, {signal.expected_move:+.1%})")
        
        print(f"\n🧠 ML Prediction:")
        ml = decision.ml_prediction
        print(f"   Direction: {ml.direction}")
        print(f"   Confidence: {ml.confidence:.1%}")
        print(f"   Expected Move: {ml.expected_move:+.1%}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_rtx_orchestrator())