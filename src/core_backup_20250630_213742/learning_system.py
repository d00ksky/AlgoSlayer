"""
AI Learning System - Track Predictions vs Reality
Learn from mistakes, improve signal weights, only trade high-conviction signals
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import asyncio
from enum import Enum

class PredictionOutcome(Enum):
    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"

class SignalType(Enum):
    TECHNICAL = "technical"
    NEWS_SENTIMENT = "news_sentiment"
    OPTIONS_FLOW = "options_flow"
    VOLATILITY = "volatility"
    MOMENTUM = "momentum"
    SECTOR_CORRELATION = "sector_correlation"
    MARKET_REGIME = "market_regime"
    MEAN_REVERSION = "mean_reversion"

@dataclass
class PredictionRecord:
    timestamp: datetime
    signal_type: SignalType
    direction: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 to 1.0
    expected_move: float  # Expected % price move
    timeframe: str  # 1h, 4h, 1d, 3d, 1w
    reasoning: str
    
    # Outcome tracking
    actual_outcome: Optional[PredictionOutcome] = None
    actual_move: Optional[float] = None
    profit_if_traded: Optional[float] = None
    evaluation_date: Optional[datetime] = None

@dataclass
class SignalPerformance:
    signal_type: SignalType
    total_predictions: int
    correct_predictions: int
    accuracy: float
    avg_confidence_when_correct: float
    avg_confidence_when_wrong: float
    avg_expected_move: float
    avg_actual_move: float
    current_weight: float
    last_updated: datetime

class LearningSystem:
    """
    AI Learning System that tracks predictions and improves over time
    """
    
    def __init__(self):
        self.predictions: List[PredictionRecord] = []
        self.signal_weights = self._initialize_weights()
        self.min_confidence_to_trade = 0.80  # Only trade 80%+ confidence
        self.learning_rate = 0.1
        
        # Performance tracking
        self.total_paper_trades = 0
        self.profitable_paper_trades = 0
        self.total_paper_pnl = 0.0
        
    def _initialize_weights(self) -> Dict[SignalType, float]:
        """Initialize equal weights for all signals"""
        num_signals = len(SignalType)
        equal_weight = 1.0 / num_signals
        return {signal: equal_weight for signal in SignalType}
    
    async def add_prediction(self, prediction: PredictionRecord):
        """Add a new prediction to track"""
        self.predictions.append(prediction)
        print(f"📝 Added prediction: {prediction.signal_type.value} - {prediction.direction} "
              f"({prediction.confidence:.2f} confidence, {prediction.expected_move:+.1f}% expected)")
    
    async def evaluate_predictions(self, current_price: float, symbol: str = "RTX"):
        """Evaluate pending predictions against actual market moves"""
        evaluated_count = 0
        
        for prediction in self.predictions:
            if prediction.actual_outcome == PredictionOutcome.PENDING:
                # Check if enough time has passed for evaluation
                time_passed = datetime.now() - prediction.timestamp
                
                should_evaluate = False
                if prediction.timeframe == "1h" and time_passed >= timedelta(hours=1):
                    should_evaluate = True
                elif prediction.timeframe == "4h" and time_passed >= timedelta(hours=4):
                    should_evaluate = True
                elif prediction.timeframe == "1d" and time_passed >= timedelta(days=1):
                    should_evaluate = True
                elif prediction.timeframe == "3d" and time_passed >= timedelta(days=3):
                    should_evaluate = True
                elif prediction.timeframe == "1w" and time_passed >= timedelta(weeks=1):
                    should_evaluate = True
                
                if should_evaluate:
                    await self._evaluate_single_prediction(prediction, current_price)
                    evaluated_count += 1
        
        if evaluated_count > 0:
            await self._update_signal_weights()
            print(f"✅ Evaluated {evaluated_count} predictions and updated weights")
    
    async def _evaluate_single_prediction(self, prediction: PredictionRecord, current_price: float):
        """Evaluate a single prediction against actual outcome"""
        # This would normally fetch historical price data
        # For simulation, we'll use the current price and some logic
        
        # Simulate actual price move (in real implementation, get from historical data)
        # For now, assume random but influenced by prediction quality
        import random
        
        # Better predictions have higher chance of being right
        if prediction.confidence > 0.8:
            actual_move = prediction.expected_move * random.uniform(0.7, 1.3)
        elif prediction.confidence > 0.6:
            actual_move = prediction.expected_move * random.uniform(0.3, 1.1)
        else:
            actual_move = prediction.expected_move * random.uniform(-0.5, 0.8)
        
        prediction.actual_move = actual_move
        prediction.evaluation_date = datetime.now()
        
        # Determine if prediction was correct
        direction_correct = False
        if prediction.direction == "BUY" and actual_move > 0:
            direction_correct = True
        elif prediction.direction == "SELL" and actual_move < 0:
            direction_correct = True
        elif prediction.direction == "HOLD" and abs(actual_move) < 0.5:
            direction_correct = True
        
        magnitude_close = abs(actual_move - prediction.expected_move) < abs(prediction.expected_move) * 0.5
        
        if direction_correct and magnitude_close:
            prediction.actual_outcome = PredictionOutcome.CORRECT
        elif direction_correct:
            prediction.actual_outcome = PredictionOutcome.PARTIAL
        else:
            prediction.actual_outcome = PredictionOutcome.INCORRECT
        
        # Calculate profit if we had traded this
        if prediction.confidence >= self.min_confidence_to_trade:
            # Simulate options trade profit/loss
            if prediction.actual_outcome == PredictionOutcome.CORRECT:
                prediction.profit_if_traded = abs(actual_move) * 500  # $500 per 1% move (options leverage)
            elif prediction.actual_outcome == PredictionOutcome.PARTIAL:
                prediction.profit_if_traded = abs(actual_move) * 200
            else:
                prediction.profit_if_traded = -200  # Typical options loss
            
            # Track paper trading performance
            self.total_paper_trades += 1
            if prediction.profit_if_traded > 0:
                self.profitable_paper_trades += 1
            self.total_paper_pnl += prediction.profit_if_traded
    
    async def _update_signal_weights(self):
        """Update signal weights based on recent performance"""
        signal_performance = {}
        
        # Calculate performance for each signal type
        for signal_type in SignalType:
            recent_predictions = [
                p for p in self.predictions 
                if p.signal_type == signal_type 
                and p.actual_outcome != PredictionOutcome.PENDING
                and p.evaluation_date and p.evaluation_date > datetime.now() - timedelta(days=30)
            ]
            
            if len(recent_predictions) < 3:  # Need minimum data
                continue
                
            correct_count = len([p for p in recent_predictions if p.actual_outcome == PredictionOutcome.CORRECT])
            partial_count = len([p for p in recent_predictions if p.actual_outcome == PredictionOutcome.PARTIAL])
            
            accuracy = (correct_count + 0.5 * partial_count) / len(recent_predictions)
            
            signal_performance[signal_type] = SignalPerformance(
                signal_type=signal_type,
                total_predictions=len(recent_predictions),
                correct_predictions=correct_count,
                accuracy=accuracy,
                avg_confidence_when_correct=sum([p.confidence for p in recent_predictions if p.actual_outcome == PredictionOutcome.CORRECT]) / max(correct_count, 1),
                avg_confidence_when_wrong=sum([p.confidence for p in recent_predictions if p.actual_outcome == PredictionOutcome.INCORRECT]) / max(len(recent_predictions) - correct_count, 1),
                avg_expected_move=sum([abs(p.expected_move) for p in recent_predictions]) / len(recent_predictions),
                avg_actual_move=sum([abs(p.actual_move or 0) for p in recent_predictions]) / len(recent_predictions),
                current_weight=self.signal_weights[signal_type],
                last_updated=datetime.now()
            )
        
        # Update weights based on performance
        total_weight = 0
        for signal_type, performance in signal_performance.items():
            # Reward accuracy and punish poor performance
            if performance.accuracy > 0.6:
                # Good performance - increase weight
                new_weight = self.signal_weights[signal_type] * (1 + self.learning_rate * (performance.accuracy - 0.5))
            else:
                # Poor performance - decrease weight
                new_weight = self.signal_weights[signal_type] * (1 - self.learning_rate * (0.5 - performance.accuracy))
            
            self.signal_weights[signal_type] = max(new_weight, 0.05)  # Minimum weight
            total_weight += self.signal_weights[signal_type]
        
        # Normalize weights
        if total_weight > 0:
            for signal_type in self.signal_weights:
                self.signal_weights[signal_type] /= total_weight
    
    def should_trade(self, combined_signal: Dict) -> Tuple[bool, str]:
        """Determine if we should trade based on signal confidence"""
        confidence = combined_signal.get('confidence', 0.0)
        direction = combined_signal.get('direction', 'HOLD')
        expected_move = combined_signal.get('expected_move', 0.0)
        
        if confidence < self.min_confidence_to_trade:
            return False, f"Confidence {confidence:.2f} below threshold {self.min_confidence_to_trade}"
        
        if abs(expected_move) < 2.0:
            return False, f"Expected move {expected_move:.1f}% too small for options trade"
        
        if direction == "HOLD":
            return False, "No directional bias"
        
        # Check if multiple signals agree
        signal_count = combined_signal.get('agreeing_signals', 0)
        if signal_count < 3:
            return False, f"Only {signal_count} signals agree, need 3+"
        
        return True, f"HIGH CONVICTION: {confidence:.1f}% confidence, {expected_move:+.1f}% expected move"
    
    def get_learning_summary(self) -> Dict:
        """Get summary of learning progress"""
        total_evaluated = len([p for p in self.predictions if p.actual_outcome != PredictionOutcome.PENDING])
        correct_evaluated = len([p for p in self.predictions if p.actual_outcome == PredictionOutcome.CORRECT])
        
        return {
            'total_predictions': len(self.predictions),
            'evaluated_predictions': total_evaluated,
            'overall_accuracy': correct_evaluated / max(total_evaluated, 1),
            'current_confidence_threshold': self.min_confidence_to_trade,
            'signal_weights': {signal.value: weight for signal, weight in self.signal_weights.items()},
            'paper_trading_stats': {
                'total_trades': self.total_paper_trades,
                'profitable_trades': self.profitable_paper_trades,
                'win_rate': self.profitable_paper_trades / max(self.total_paper_trades, 1),
                'total_pnl': self.total_paper_pnl,
                'avg_pnl_per_trade': self.total_paper_pnl / max(self.total_paper_trades, 1)
            }
        }
    
    async def daily_report(self) -> str:
        """Generate daily learning report"""
        summary = self.get_learning_summary()
        
        report = f"""
📊 **DAILY AI LEARNING REPORT**
═══════════════════════════════

📈 **Prediction Performance:**
• Total Predictions: {summary['total_predictions']}
• Evaluated: {summary['evaluated_predictions']}
• Overall Accuracy: {summary['overall_accuracy']:.1f}%

💼 **Paper Trading Results:**
• Total Trades: {summary['paper_trading_stats']['total_trades']}
• Win Rate: {summary['paper_trading_stats']['win_rate']:.1f}%
• Total P&L: ${summary['paper_trading_stats']['total_pnl']:.0f}
• Avg per Trade: ${summary['paper_trading_stats']['avg_pnl_per_trade']:.0f}

⚖️ **Signal Weights (Top 3):**
"""
        
        # Sort signals by weight
        sorted_signals = sorted(self.signal_weights.items(), key=lambda x: x[1], reverse=True)
        for signal, weight in sorted_signals[:3]:
            report += f"• {signal.value}: {weight:.1f}%\n"
        
        report += f"\n🎯 **Trading Threshold:** {self.min_confidence_to_trade:.0%} confidence required"
        
        return report

# Global learning system instance
learning_system = LearningSystem()