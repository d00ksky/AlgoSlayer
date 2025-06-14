"""
RTX Trading System Scheduler
Main orchestration engine for autonomous trading
"""
import asyncio
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
from loguru import logger

from config.trading_config import config, TradingModeConfig
from src.core.ibkr_manager import ibkr_manager
from src.core.telegram_bot import telegram_bot
from src.core.accelerated_learning import learning_engine
from src.core.performance_tracker import performance_tracker
# Use Signal Fusion Engine for centralized signal management
from src.core.signal_fusion import SignalFusionEngine

class RTXTradingScheduler:
    """Main scheduler for autonomous RTX trading"""
    
    def __init__(self):
        self.running = False
        self.start_time = None
        self.trading_mode = TradingModeConfig.load_from_env()
        
        # Initialize AI signals using centralized Signal Fusion Engine
        # This ensures future signal additions automatically work everywhere
        self.signal_fusion = SignalFusionEngine()
        
        # Convert to scheduler format for backward compatibility
        self.signals = {}
        for signal in self.signal_fusion.signals:
            # Use signal's name attribute, fallback to signal_name, or class name
            name = getattr(signal, 'name', None) or getattr(signal, 'signal_name', signal.__class__.__name__)
            self.signals[name] = signal
        
        logger.success(f"✅ Loaded {len(self.signals)} AI signals from Signal Fusion Engine")
        
        # Trading state
        self.last_prediction = None
        self.prediction_count = 0
        self.accuracy_tracker = []
        
        logger.info("🤖 RTX Trading Scheduler initialized")
        logger.info(f"📊 Mode: {self.trading_mode.get_mode_description()}")
    
    async def start(self) -> None:
        """Start the trading system"""
        
        if self.running:
            logger.warning("⚠️ Scheduler already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 Starting RTX Trading System...")
        
        # Send startup notification
        await telegram_bot.send_system_startup(self.trading_mode.get_mode_description())
        
        # Initialize connections
        await self._initialize_connections()
        
        # Start main trading loop
        await self._main_trading_loop()
    
    async def _initialize_connections(self) -> None:
        """Initialize all system connections"""
        
        logger.info("🔌 Initializing system connections...")
        
        # Connect to IBKR if needed
        if self.trading_mode.should_connect_ibkr():
            await ibkr_manager.connect()
        
        # Test Telegram bot
        await telegram_bot.test_connection()
        
        # Quick learning system test
        if config.learning.TRACK_ACCURACY:
            logger.info("🧠 Testing accelerated learning system...")
            await learning_engine.learn_from_historical_data("RTX", 1)
        
        logger.success("✅ System initialization complete")
    
    async def _main_trading_loop(self) -> None:
        """Main prediction and trading loop"""
        
        logger.info(f"🔄 Starting main trading loop (every {config.PREDICTION_INTERVAL_MINUTES} minutes)")
        
        while self.running:
            try:
                # Check if market is open (optional - crypto/forex trades 24/7)
                if self._is_market_hours():
                    await self._run_prediction_cycle()
                else:
                    logger.info("🌙 Outside market hours - running analysis only")
                    await self._run_analysis_only()
                
                # Wait for next cycle
                await asyncio.sleep(config.PREDICTION_INTERVAL_MINUTES * 60)
                
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}")
                await telegram_bot.send_error_alert({
                    "type": "Main Loop Error",
                    "message": str(e),
                    "severity": "HIGH"
                })
                
                # Brief pause before continuing
                await asyncio.sleep(60)
    
    async def _run_prediction_cycle(self) -> None:
        """Run complete prediction and trading cycle"""
        
        logger.info("🎯 Running prediction cycle...")
        
        # Get market data
        market_data = await ibkr_manager.get_market_data("RTX")
        current_price = market_data.get("price", 0)
        
        if current_price == 0:
            logger.warning("⚠️ No price data available")
            return
        
        # Run AI signals in parallel
        signal_results = await self._run_ai_signals()
        
        # Aggregate signals
        prediction = self._aggregate_signals(signal_results, current_price)
        
        # Record prediction for learning
        await performance_tracker.record_prediction(
            direction=prediction["direction"],
            confidence=prediction["confidence"],
            signal_data=signal_results,
            reasoning=prediction["reasoning"]
        )
        
        # Send prediction notification
        await telegram_bot.send_prediction_alert(prediction)
        
        # Execute trade if confidence is high enough
        if prediction["confidence"] > config.CONFIDENCE_THRESHOLD:
            await self._execute_trade_decision(prediction)
        
        # Update tracking
        self.last_prediction = prediction
        self.prediction_count += 1
        
        logger.success(f"✅ Prediction cycle complete: {prediction['direction']} ({prediction['confidence']:.1%})")
    
    async def _run_analysis_only(self) -> None:
        """Run analysis without trading (after hours)"""
        
        # Run accelerated learning
        if self.prediction_count % 4 == 0:  # Every 4th cycle
            await learning_engine.learn_from_historical_data("RTX", 1)
        
        # Run basic signal analysis
        signal_results = await self._run_ai_signals()
        
        logger.info("📊 After-hours analysis complete")
    
    async def _run_ai_signals(self) -> Dict:
        """Run all AI signals in parallel"""
        
        logger.info("🤖 Running AI signal analysis...")
        
        # Run signals in parallel for speed
        tasks = []
        for name, signal in self.signals.items():
            tasks.append(signal.analyze("RTX"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        signal_results = {}
        for i, (name, signal) in enumerate(self.signals.items()):
            if isinstance(results[i], Exception):
                logger.error(f"❌ Signal {name} failed: {results[i]}")
                signal_results[name] = self._create_neutral_signal(name)
            else:
                signal_results[name] = results[i]
        
        logger.info(f"📊 Analyzed {len(signal_results)} AI signals")
        return signal_results
    
    def _aggregate_signals(self, signal_results: Dict, current_price: float) -> Dict:
        """Aggregate multiple AI signals into trading decision"""
        
        buy_strength = 0
        sell_strength = 0
        total_confidence = 0
        signal_count = 0
        reasoning_parts = []
        
        # Combine signals
        for name, signal in signal_results.items():
            direction = signal.get("direction", "HOLD")
            strength = signal.get("strength", 0)
            confidence = signal.get("confidence", 0)
            
            if direction == "BUY":
                buy_strength += strength
            elif direction == "SELL":
                sell_strength += strength
            
            total_confidence += confidence
            signal_count += 1
            
            # Add to reasoning
            if strength > 0.1:
                reasoning_parts.append(f"{name}: {direction} ({confidence:.1%})")
        
        # Determine overall direction
        strength_diff = abs(buy_strength - sell_strength)
        total_strength = buy_strength + sell_strength
        
        # Require meaningful signal strength and agreement
        if buy_strength > sell_strength and buy_strength > 0.3 and strength_diff > 0.2:
            final_direction = "BUY"
            # Confidence based on signal agreement and total strength
            signal_agreement = strength_diff / max(total_strength, 0.1)
            final_confidence = min(0.95, signal_agreement * total_strength)
        elif sell_strength > buy_strength and sell_strength > 0.3 and strength_diff > 0.2:
            final_direction = "SELL"
            # Confidence based on signal agreement and total strength
            signal_agreement = strength_diff / max(total_strength, 0.1)
            final_confidence = min(0.95, signal_agreement * total_strength)
        else:
            final_direction = "HOLD"
            final_confidence = 0.5
        
        # Create prediction
        prediction = {
            "symbol": "RTX",
            "current_price": current_price,
            "direction": final_direction,
            "confidence": final_confidence,
            "buy_strength": buy_strength,
            "sell_strength": sell_strength,
            "signals_analyzed": signal_count,
            "reasoning": "; ".join(reasoning_parts[:3]) if reasoning_parts else "Neutral market conditions",
            "timestamp": datetime.now().isoformat()
        }
        
        return prediction
    
    async def _execute_trade_decision(self, prediction: Dict) -> None:
        """Execute trade if conditions are met"""
        
        direction = prediction["direction"]
        confidence = prediction["confidence"]
        current_price = prediction["current_price"]
        
        # Check if we should trade
        if not self.trading_mode.is_safe_to_trade():
            logger.info(f"📊 Trade signal: {direction} ({confidence:.1%}) - Trading disabled")
            return
        
        if confidence < config.HIGH_CONFIDENCE_THRESHOLD:
            logger.info(f"📊 Trade signal: {direction} ({confidence:.1%}) - Below high confidence threshold")
            return
        
        # Calculate position size
        position_size = min(config.MAX_POSITION_SIZE, config.STARTING_CAPITAL * 0.1)
        quantity = int(position_size / current_price)
        
        if quantity == 0:
            logger.warning("⚠️ Position size too small to trade")
            return
        
        # Send high confidence alert
        await telegram_bot.send_high_confidence_trade_alert({
            "symbol": "RTX",
            "action": direction,
            "price": current_price,
            "confidence": confidence,
            "position_size": position_size,
            "target_price": current_price * (1.05 if direction == "BUY" else 0.95),
            "stop_loss": current_price * (0.95 if direction == "BUY" else 1.05)
        })
        
        # Execute order
        order_data = {
            "symbol": "RTX",
            "action": direction,
            "quantity": quantity,
            "type": "MKT"
        }
        
        execution_result = await ibkr_manager.place_order(order_data)
        
        # Send execution notification
        await telegram_bot.send_trade_execution({
            "symbol": "RTX",
            "action": direction,
            "quantity": quantity,
            "price": current_price,
            "order_type": "MARKET",
            "status": execution_result.get("status", "UNKNOWN")
        })
        
        logger.success(f"🎯 Trade executed: {direction} {quantity} RTX @ ${current_price:.2f}")
    
    def _is_market_hours(self) -> bool:
        """Check if market is currently open"""
        # Use Eastern Time for US markets
        import pytz
        eastern = pytz.timezone('US/Eastern')
        current_time = datetime.now(eastern).time()
        return config.MARKET_OPEN <= current_time <= config.MARKET_CLOSE
    
    def _create_neutral_signal(self, signal_name: str) -> Dict:
        """Create neutral signal for failed signals"""
        return {
            "signal_name": signal_name,
            "direction": "HOLD",
            "strength": 0.1,
            "confidence": 0.5,
            "reasoning": "Signal analysis failed",
            "timestamp": datetime.now().isoformat()
        }
    
    async def stop(self) -> None:
        """Stop the trading system"""
        
        logger.info("🛑 Stopping RTX Trading System...")
        
        self.running = False
        
        # Disconnect from IBKR
        await ibkr_manager.disconnect()
        
        # Send shutdown notification
        uptime = str(datetime.now() - self.start_time) if self.start_time else "Unknown"
        
        await telegram_bot.send_message(f"""
🛑 <b>RTX TRADING SYSTEM SHUTDOWN</b>

⏱️ <b>Uptime:</b> {uptime}
📊 <b>Predictions Made:</b> {self.prediction_count}
💰 <b>Mode:</b> {self.trading_mode.get_mode_description()}

<i>System offline</i>
        """)
        
        logger.info("✅ Trading system stopped")
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        uptime = str(datetime.now() - self.start_time) if self.start_time else "Not started"
        
        return {
            "running": self.running,
            "uptime": uptime,
            "trading_mode": self.trading_mode.get_mode_description(),
            "predictions_made": self.prediction_count,
            "last_prediction": self.last_prediction,
            "ibkr_status": ibkr_manager.get_connection_status(),
            "signals_count": len(self.signals),
            "market_hours": self._is_market_hours()
        }

# Global scheduler instance
scheduler = RTXTradingScheduler() 