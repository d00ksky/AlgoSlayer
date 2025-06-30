"""
Small-Capital RTX Trading Strategy
Optimized for ~$1200-1350 capital (9 RTX shares)
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from loguru import logger
import yfinance as yf
import numpy as np

class PositionType(Enum):
    CORE_HOLD = "core_hold"  # Long-term hold shares
    SWING_TRADE = "swing_trade"  # Trading shares
    COVERED_CALL = "covered_call"  # Sold calls against shares
    CASH = "cash"  # Available cash

class TradeAction(Enum):
    BUY_SHARES = "buy_shares"
    SELL_SHARES = "sell_shares"
    SELL_COVERED_CALL = "sell_covered_call"
    BUY_TO_CLOSE_CALL = "buy_to_close_call"
    HOLD = "hold"

@dataclass
class Position:
    position_type: PositionType
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    date_opened: datetime

@dataclass
class TradeSignal:
    action: TradeAction
    quantity: int
    reasoning: str
    confidence: float
    expected_profit: float
    risk_level: str
    timeframe: str

class SmallCapitalStrategy:
    """
    Trading strategy optimized for $1000 capital
    Pure share swing trading with AI-driven timing
    """
    
    def __init__(self, starting_capital: float = 1000):
        self.starting_capital = starting_capital
        self.current_capital = starting_capital
        self.rtx_price = 0.0
        
        # Position allocation for $1000 capital
        self.max_total_shares = 6  # ~$900 at $150/share
        self.core_position = 4  # Hold 4 shares as base
        self.swing_shares = 2  # Trade with 2 shares
        self.cash_buffer = 100  # Keep $100 cash for opportunities
        
        # Risk management
        self.max_position_risk = 0.10  # 10% max loss per trade
        self.daily_loss_limit = 30  # $30 max daily loss
        self.swing_stop_loss = 0.02  # 2% stop loss on swing trades
        self.profit_target = 0.015  # 1.5% profit target
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.trades_today = 0
        self.max_daily_trades = 2  # Max 2 trades per day
        
    async def analyze_market_conditions(self) -> Dict:
        """Analyze current RTX market conditions"""
        try:
            # Get RTX data
            rtx = yf.Ticker("RTX")
            hist = rtx.history(period="5d", interval="1h")
            
            if hist.empty:
                return {"status": "no_data"}
            
            current_price = hist['Close'].iloc[-1]
            self.rtx_price = current_price
            
            # Calculate key metrics
            volatility = hist['Close'].pct_change().std() * np.sqrt(252)  # Annualized
            volume_avg = hist['Volume'].mean()
            volume_current = hist['Volume'].iloc[-1]
            volume_ratio = volume_current / volume_avg if volume_avg > 0 else 1
            
            # Price momentum
            price_change_1h = (current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]
            price_change_24h = (current_price - hist['Close'].iloc[-24]) / hist['Close'].iloc[-24] if len(hist) >= 24 else 0
            
            # Support/resistance levels
            high_5d = hist['High'].max()
            low_5d = hist['Low'].min()
            resistance_distance = (high_5d - current_price) / current_price
            support_distance = (current_price - low_5d) / current_price
            
            return {
                "status": "success",
                "current_price": current_price,
                "volatility": volatility,
                "volume_ratio": volume_ratio,
                "price_change_1h": price_change_1h,
                "price_change_24h": price_change_24h,
                "resistance_distance": resistance_distance,
                "support_distance": support_distance,
                "high_5d": high_5d,
                "low_5d": low_5d
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {"status": "error", "error": str(e)}
    
    async def generate_trade_signal(self, market_data: Dict, ai_predictions: Dict) -> TradeSignal:
        """Generate trading signal based on market conditions and AI predictions"""
        
        if market_data.get("status") != "success":
            return TradeSignal(
                action=TradeAction.HOLD,
                quantity=0,
                reasoning="No market data available",
                confidence=0.0,
                expected_profit=0.0,
                risk_level="low",
                timeframe="none"
            )
        
        current_price = market_data["current_price"]
        ai_confidence = ai_predictions.get("confidence", 0.5)
        ai_direction = ai_predictions.get("direction", "HOLD")
        
        # Check if we should trade today (risk management)
        if self.daily_pnl <= -self.daily_loss_limit:
            return TradeSignal(
                action=TradeAction.HOLD,
                quantity=0,
                reasoning="Daily loss limit reached",
                confidence=0.0,
                expected_profit=0.0,
                risk_level="high",
                timeframe="none"
            )
        
        if self.trades_today >= self.max_daily_trades:
            return TradeSignal(
                action=TradeAction.HOLD,
                quantity=0,
                reasoning="Daily trade limit reached",
                confidence=0.0,
                expected_profit=0.0,
                risk_level="medium",
                timeframe="none"
            )
        
        # Determine best action based on conditions
        return await self._determine_optimal_action(market_data, ai_predictions)
    
    async def _determine_optimal_action(self, market_data: Dict, ai_predictions: Dict) -> TradeSignal:
        """Determine the optimal trading action"""
        
        current_price = market_data["current_price"]
        volatility = market_data["volatility"]
        ai_confidence = ai_predictions.get("confidence", 0.5)
        ai_direction = ai_predictions.get("direction", "HOLD")
        
        # High confidence bullish signal - buy shares
        if ai_direction == "BUY" and ai_confidence > 0.75:
            available_cash = self.current_capital - (self.core_position * current_price)
            max_shares = min(self.swing_shares, int(available_cash / current_price))
            
            if max_shares > 0:
                return TradeSignal(
                    action=TradeAction.BUY_SHARES,
                    quantity=1,  # Buy 1 share at a time
                    reasoning=f"High confidence bullish signal ({ai_confidence:.2f})",
                    confidence=ai_confidence,
                    expected_profit=current_price * self.profit_target,
                    risk_level="medium",
                    timeframe="1-2 days"
                )
        
        # High confidence bearish signal - sell shares
        elif ai_direction == "SELL" and ai_confidence > 0.75:
            return TradeSignal(
                action=TradeAction.SELL_SHARES,
                quantity=1,  # Sell 1 share at a time
                reasoning=f"High confidence bearish signal ({ai_confidence:.2f})",
                confidence=ai_confidence,
                expected_profit=current_price * self.profit_target,
                risk_level="medium",
                timeframe="1-2 days"
            )
        
        # Medium confidence scalping opportunity
        elif ai_confidence > 0.65 and market_data.get("volume_ratio", 1) > 1.5:
            return await self._evaluate_scalping_opportunity(market_data, ai_predictions)
        
        # Default to hold
        return TradeSignal(
            action=TradeAction.HOLD,
            quantity=0,
            reasoning="No clear signal or opportunity",
            confidence=0.5,
            expected_profit=0.0,
            risk_level="low",
            timeframe="waiting"
        )
    
    async def _evaluate_scalping_opportunity(self, market_data: Dict, ai_predictions: Dict) -> TradeSignal:
        """Evaluate short-term scalping opportunities"""
        
        try:
            current_price = market_data["current_price"]
            price_change_1h = market_data.get("price_change_1h", 0)
            ai_direction = ai_predictions.get("direction", "HOLD")
            ai_confidence = ai_predictions.get("confidence", 0.5)
            
            # Look for quick reversal opportunities
            if abs(price_change_1h) > 0.01:  # >1% move in 1 hour
                if ai_direction == "BUY" and price_change_1h < -0.01:  # Oversold bounce
                    return TradeSignal(
                        action=TradeAction.BUY_SHARES,
                        quantity=1,
                        reasoning=f"Oversold scalp opportunity - {price_change_1h:.2f}% 1h drop",
                        confidence=ai_confidence * 0.8,  # Lower confidence for scalping
                        expected_profit=current_price * 0.01,  # 1% quick target
                        risk_level="high",
                        timeframe="2-4 hours"
                    )
                elif ai_direction == "SELL" and price_change_1h > 0.01:  # Overbought fade
                    return TradeSignal(
                        action=TradeAction.SELL_SHARES,
                        quantity=1,
                        reasoning=f"Overbought scalp opportunity - {price_change_1h:.2f}% 1h rally",
                        confidence=ai_confidence * 0.8,
                        expected_profit=current_price * 0.01,
                        risk_level="high",
                        timeframe="2-4 hours"
                    )
        
        except Exception as e:
            logger.error(f"Error evaluating scalping: {e}")
        
        return TradeSignal(
            action=TradeAction.HOLD,
            quantity=0,
            reasoning="No scalping opportunity",
            confidence=0.0,
            expected_profit=0.0,
            risk_level="low",
            timeframe="none"
        )
    
    def calculate_position_size(self, action: TradeAction, confidence: float) -> int:
        """Calculate optimal position size based on Kelly Criterion"""
        
        if action == TradeAction.HOLD:
            return 0
        
        # Simplified Kelly Criterion
        win_probability = confidence
        avg_win = 0.02  # 2% average win
        avg_loss = 0.02  # 2% average loss
        
        kelly_fraction = (win_probability * avg_win - (1 - win_probability) * avg_loss) / avg_win
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        
        if action in [TradeAction.BUY_SHARES, TradeAction.SELL_SHARES]:
            # For small capital, always trade 1 share at a time
            return 1
        
        return 0
    
    def update_performance(self, realized_pnl: float, unrealized_pnl: float):
        """Update performance metrics"""
        self.daily_pnl += realized_pnl
        self.total_pnl += realized_pnl
        self.trades_today += 1
        
        logger.info(f"Performance Update - Daily P&L: ${self.daily_pnl:.2f}, Total P&L: ${self.total_pnl:.2f}")
    
    def reset_daily_metrics(self):
        """Reset daily tracking metrics"""
        self.daily_pnl = 0.0
        self.trades_today = 0
        logger.info("Daily metrics reset")
    
    def get_strategy_summary(self) -> Dict:
        """Get current strategy status"""
        return {
            "strategy_name": "Small Capital RTX Focus",
            "starting_capital": self.starting_capital,
            "current_capital": self.current_capital,
            "total_pnl": self.total_pnl,
            "daily_pnl": self.daily_pnl,
            "max_shares": self.max_total_shares,
            "core_position": self.core_position,
            "swing_shares": self.swing_shares,
            "trades_today": self.trades_today,
            "rtx_price": self.rtx_price
        }