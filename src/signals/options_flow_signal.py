"""
Options Flow Analysis Signal
Track unusual options activity and smart money moves
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

from config.trading_config import config

class OptionsFlowSignal:
    """Analyze options flow for RTX smart money signals"""
    
    def __init__(self):
        self.signal_name = "options_flow"
        self.weight = config.SIGNAL_WEIGHTS.get(self.signal_name, 0.15)
        self.last_analysis = None
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze options flow for trading signals"""
        
        try:
            # Get options data
            options_data = await self._get_options_data(symbol)
            
            if not options_data:
                return self._create_neutral_signal("No options data available")
            
            # Analyze options flow
            flow_analysis = self._analyze_options_flow(options_data)
            
            # Generate signal
            signal = self._generate_signal(flow_analysis)
            
            self.last_analysis = signal
            return signal
            
        except Exception as e:
            logger.error(f"📊 Options flow error: {e}")
            return self._create_neutral_signal(f"Analysis error: {str(e)}")
    
    async def _get_options_data(self, symbol: str) -> Optional[Dict]:
        """Get options chain data"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current price for context
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            # Get options expiration dates
            expirations = ticker.options
            
            if not expirations:
                logger.warning(f"📊 No options data for {symbol}")
                return None
            
            # Use nearest expiration (usually most liquid)
            nearest_exp = expirations[0]
            
            # Get options chain
            chain = ticker.option_chain(nearest_exp)
            calls = chain.calls
            puts = chain.puts
            
            logger.info(f"📊 Options data: {len(calls)} calls, {len(puts)} puts for {nearest_exp}")
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "expiration": nearest_exp,
                "calls": calls,
                "puts": puts
            }
            
        except Exception as e:
            logger.error(f"📊 Options data error: {e}")
            return None
    
    def _analyze_options_flow(self, options_data: Dict) -> Dict:
        """Analyze options activity for smart money signals"""
        
        calls = options_data["calls"]
        puts = options_data["puts"]
        current_price = options_data["current_price"]
        
        analysis = {
            "current_price": current_price,
            "total_call_volume": 0,
            "total_put_volume": 0,
            "call_put_ratio": 0,
            "unusual_activity": [],
            "smart_money_signals": []
        }
        
        # Calculate total volumes
        call_volume = calls['volume'].fillna(0).sum()
        put_volume = puts['volume'].fillna(0).sum()
        
        analysis["total_call_volume"] = int(call_volume)
        analysis["total_put_volume"] = int(put_volume)
        
        # Call/Put ratio
        if put_volume > 0:
            analysis["call_put_ratio"] = call_volume / put_volume
        else:
            analysis["call_put_ratio"] = float('inf') if call_volume > 0 else 0
        
        # Analyze unusual activity
        analysis["unusual_activity"] = self._find_unusual_activity(calls, puts, current_price)
        
        # Look for smart money signals
        analysis["smart_money_signals"] = self._identify_smart_money(calls, puts, current_price)
        
        # Calculate overall sentiment
        analysis["sentiment"] = self._calculate_options_sentiment(analysis)
        
        return analysis
    
    def _find_unusual_activity(self, calls: pd.DataFrame, puts: pd.DataFrame, current_price: float) -> List[Dict]:
        """Find unusual options activity"""
        
        unusual_activity = []
        
        # Define unusual volume threshold (top 10% of activity)
        all_volumes = pd.concat([
            calls['volume'].fillna(0),
            puts['volume'].fillna(0)
        ])
        
        volume_threshold = all_volumes.quantile(0.9) if len(all_volumes) > 0 else 0
        
        # Check calls for unusual activity
        for _, option in calls.iterrows():
            volume = option.get('volume', 0) or 0
            
            if volume > volume_threshold and volume > 100:  # Significant volume
                distance_from_money = abs(option['strike'] - current_price) / current_price
                
                unusual_activity.append({
                    "type": "CALL",
                    "strike": option['strike'],
                    "volume": int(volume),
                    "open_interest": int(option.get('openInterest', 0) or 0),
                    "distance_from_money": distance_from_money,
                    "in_the_money": option['strike'] < current_price
                })
        
        # Check puts for unusual activity
        for _, option in puts.iterrows():
            volume = option.get('volume', 0) or 0
            
            if volume > volume_threshold and volume > 100:
                distance_from_money = abs(option['strike'] - current_price) / current_price
                
                unusual_activity.append({
                    "type": "PUT",
                    "strike": option['strike'],
                    "volume": int(volume),
                    "open_interest": int(option.get('openInterest', 0) or 0),
                    "distance_from_money": distance_from_money,
                    "in_the_money": option['strike'] > current_price
                })
        
        # Sort by volume
        unusual_activity.sort(key=lambda x: x['volume'], reverse=True)
        
        return unusual_activity[:10]  # Top 10 unusual activities
    
    def _identify_smart_money(self, calls: pd.DataFrame, puts: pd.DataFrame, current_price: float) -> List[str]:
        """Identify smart money patterns"""
        
        signals = []
        
        # Large block trades (institutional activity)
        large_call_trades = calls[calls['volume'].fillna(0) > 500]
        large_put_trades = puts[puts['volume'].fillna(0) > 500]
        
        if len(large_call_trades) > len(large_put_trades):
            signals.append("Large call block trades detected (bullish institutions)")
        elif len(large_put_trades) > len(large_call_trades):
            signals.append("Large put block trades detected (bearish institutions)")
        
        # Dark pool activity indicators
        # High open interest vs volume ratio suggests accumulation
        calls['oi_volume_ratio'] = calls['openInterest'] / (calls['volume'].fillna(0) + 1)
        puts['oi_volume_ratio'] = puts['openInterest'] / (puts['volume'].fillna(0) + 1)
        
        high_oi_calls = calls[calls['oi_volume_ratio'] > 5].shape[0]
        high_oi_puts = puts[puts['oi_volume_ratio'] > 5].shape[0]
        
        if high_oi_calls > high_oi_puts * 1.5:
            signals.append("Call accumulation pattern (stealth bullish)")
        elif high_oi_puts > high_oi_calls * 1.5:
            signals.append("Put accumulation pattern (stealth bearish)")
        
        # Sweep activity (aggressive buying/selling)
        # Look for options trading significantly above bid/ask midpoint
        for _, call in calls.iterrows():
            last_price = call.get('lastPrice', 0)
            bid = call.get('bid', 0)
            ask = call.get('ask', 0)
            
            if ask > 0 and last_price >= ask * 0.95:  # Bought near ask
                volume = call.get('volume', 0) or 0
                if volume > 200:
                    signals.append(f"Call sweep at ${call['strike']} (aggressive buying)")
                    break
        
        return signals
    
    def _calculate_options_sentiment(self, analysis: Dict) -> str:
        """Calculate overall options sentiment"""
        
        call_volume = analysis["total_call_volume"]
        put_volume = analysis["total_put_volume"]
        call_put_ratio = analysis["call_put_ratio"]
        unusual_activity = analysis["unusual_activity"]
        smart_money_signals = analysis["smart_money_signals"]
        
        # Volume-based sentiment
        if call_put_ratio > 1.5:
            volume_sentiment = "bullish"
        elif call_put_ratio < 0.7:
            volume_sentiment = "bearish"
        else:
            volume_sentiment = "neutral"
        
        # Unusual activity sentiment
        call_unusual = sum(1 for activity in unusual_activity if activity["type"] == "CALL")
        put_unusual = sum(1 for activity in unusual_activity if activity["type"] == "PUT")
        
        if call_unusual > put_unusual:
            unusual_sentiment = "bullish"
        elif put_unusual > call_unusual:
            unusual_sentiment = "bearish"
        else:
            unusual_sentiment = "neutral"
        
        # Smart money sentiment
        bullish_smart_signals = sum(1 for signal in smart_money_signals if "bullish" in signal.lower())
        bearish_smart_signals = sum(1 for signal in smart_money_signals if "bearish" in signal.lower())
        
        if bullish_smart_signals > bearish_smart_signals:
            smart_sentiment = "bullish"
        elif bearish_smart_signals > bullish_smart_signals:
            smart_sentiment = "bearish"
        else:
            smart_sentiment = "neutral"
        
        # Combine sentiments
        bullish_votes = [volume_sentiment, unusual_sentiment, smart_sentiment].count("bullish")
        bearish_votes = [volume_sentiment, unusual_sentiment, smart_sentiment].count("bearish")
        
        if bullish_votes > bearish_votes:
            return "bullish"
        elif bearish_votes > bullish_votes:
            return "bearish"
        else:
            return "neutral"
    
    def _generate_signal(self, flow_analysis: Dict) -> Dict:
        """Generate trading signal from options flow analysis"""
        
        sentiment = flow_analysis.get("sentiment", "neutral")
        call_put_ratio = flow_analysis.get("call_put_ratio", 1.0)
        unusual_activity = flow_analysis.get("unusual_activity", [])
        smart_money_signals = flow_analysis.get("smart_money_signals", [])
        
        # Calculate confidence based on multiple factors
        confidence = 0.5  # Base confidence
        
        # Call/put ratio confidence
        if call_put_ratio > 2.0 or call_put_ratio < 0.5:
            confidence += 0.2  # Strong ratio = higher confidence
        
        # Unusual activity confidence
        if len(unusual_activity) > 3:
            confidence += 0.15
        
        # Smart money confidence
        if len(smart_money_signals) > 0:
            confidence += 0.15
        
        confidence = min(0.95, confidence)  # Cap at 95%
        
        # Convert sentiment to trading signal
        if sentiment == "bullish" and confidence > 0.6:
            direction = "BUY"
            signal_strength = confidence * self.weight
        elif sentiment == "bearish" and confidence > 0.6:
            direction = "SELL"
            signal_strength = confidence * self.weight
        else:
            direction = "HOLD"
            signal_strength = 0.1
        
        # Create reasoning
        reasoning = f"Options flow: {sentiment} sentiment"
        if call_put_ratio != 1.0:
            reasoning += f", C/P ratio: {call_put_ratio:.1f}"
        if unusual_activity:
            reasoning += f", {len(unusual_activity)} unusual activities"
        if smart_money_signals:
            reasoning += f", smart money: {smart_money_signals[0][:30]}..."
        
        return {
            "signal_name": self.signal_name,
            "direction": direction,
            "strength": signal_strength,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "raw_data": flow_analysis
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
            "status": "operational"
        } 