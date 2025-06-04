"""
Base Signal Interface
All AI signals inherit from this for consistent architecture
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import asyncio

class SignalResult(BaseModel):
    """Standard signal result format"""
    signal_name: str
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    direction: str  # "BUY", "SELL", "HOLD"
    reasoning: str
    data: Optional[Dict[str, Any]] = None
    trade_type: Optional[str] = None  # "CALL", "PUT", "STOCK"
    expiry_suggestion: Optional[str] = None
    strike_suggestion: Optional[float] = None

class BaseSignal(ABC):
    """Base class for all AI trading signals"""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.enabled = True
        self.last_signal: Optional[SignalResult] = None
    
    @abstractmethod
    async def analyze(self, symbol: str) -> SignalResult:
        """
        Analyze the symbol and return a signal
        Must be implemented by all signal classes
        """
        pass
    
    @abstractmethod
    async def backtest(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Backtest this signal strategy
        Returns performance metrics
        """
        pass
    
    def set_weight(self, weight: float):
        """Adjust signal weight"""
        self.weight = max(0.0, min(1.0, weight))
    
    def enable(self):
        """Enable this signal"""
        self.enabled = True
    
    def disable(self):
        """Disable this signal"""
        self.enabled = False
    
    async def get_signal_if_enabled(self, symbol: str) -> Optional[SignalResult]:
        """Get signal only if enabled"""
        if not self.enabled:
            return None
        
        try:
            signal = await self.analyze(symbol)
            signal.confidence *= self.weight  # Apply weight
            self.last_signal = signal
            return signal
        except Exception as e:
            print(f"Error in {self.name}: {e}")
            return None 