"""
Options Trading Scheduler
Enhanced scheduler that focuses on options predictions and trading
Integrates all AI signals with options-specific logic
"""
import asyncio
import json
import sqlite3
from datetime import datetime, time as dt_time, timedelta, date
from typing import Dict, List, Optional
from loguru import logger

from config.trading_config import config, TradingModeConfig
from config.options_config import options_config
from src.core.telegram_bot import telegram_bot
from src.core.notification_center import notification_center
from src.core.options_data_engine import options_data_engine
from src.core.options_prediction_engine import options_prediction_engine
from src.core.options_paper_trader import options_paper_trader
from src.core.prediction_outcome_tracker import outcome_tracker
from src.core.signal_effectiveness_tracker import signal_tracker
from src.core.kelly_criterion_optimizer import kelly_optimizer
from src.core.iv_rank_optimizer import iv_rank_optimizer
from src.core.rtx_earnings_calendar import rtx_earnings_calendar
from src.core.multi_timeframe_confirmation import multi_timeframe_confirmation

# Import all AI signals
from src.signals.news_sentiment_signal import NewsSentimentSignal
from src.signals.technical_analysis_signal import TechnicalAnalysisSignal
from src.signals.options_flow_signal import OptionsFlowSignal
from src.signals.volatility_analysis_signal import VolatilityAnalysisSignal
from src.signals.momentum_signal import MomentumSignal
from src.signals.sector_correlation_signal import SectorCorrelationSignal
from src.signals.mean_reversion_signal import MeanReversionSignal
from src.signals.market_regime_signal import MarketRegimeSignal

# Import new high-value options signals
from src.signals.trump_geopolitical_signal import TrumpGeopoliticalSignal
from src.signals.defense_contract_signal import DefenseContractSignal
from src.signals.rtx_earnings_signal import RTXEarningsSignal
from src.signals.options_iv_percentile_signal import OptionsIVPercentileSignal

class OptionsScheduler:
    """Advanced scheduler for autonomous RTX options trading"""
    
    def __init__(self):
        self.running = False
        self.start_time = None
        self.trading_mode = TradingModeConfig.load_from_env()
        
        self.strategy_id = "options_single"  # Default, can be overridden
        # Initialize AI signals with adaptive weights (12 signals total)
        self.signal_weights = {
            # Classic signals (rebalanced)
            "news_sentiment": 0.10,
            "technical_analysis": 0.12,
            "options_flow": 0.12,
            "volatility_analysis": 0.08,
            "momentum": 0.08,
            "sector_correlation": 0.08,
            "mean_reversion": 0.08,
            "market_regime": 0.10,
            
            # New high-value options signals
            "trump_geopolitical": 0.08,  # Political impact on defense
            "defense_contract": 0.06,    # Government contracts
            "rtx_earnings": 0.05,        # Earnings timing & IV
            "options_iv_percentile": 0.05 # IV rank analysis
        }
        
        self.signals = {
            # Classic signals
            "news_sentiment": NewsSentimentSignal(),
            "technical_analysis": TechnicalAnalysisSignal(),
            "options_flow": OptionsFlowSignal(),
            "volatility_analysis": VolatilityAnalysisSignal(),
            "momentum": MomentumSignal(),
            "sector_correlation": SectorCorrelationSignal(),
            "mean_reversion": MeanReversionSignal(),
            "market_regime": MarketRegimeSignal(),
            
            # New high-value options signals
            "trump_geopolitical": TrumpGeopoliticalSignal(),
            "defense_contract": DefenseContractSignal(),
            "rtx_earnings": RTXEarningsSignal(),
            "options_iv_percentile": OptionsIVPercentileSignal()
        }
        
        # Options trading state
        self.last_options_prediction = None
        self.prediction_count = 0
        self.cycle_count = 0
        self.telemetry_db = "data/options_performance.db"

        # Market open status tracking
        self.market_open_message_sent = False
        self.last_market_open_date = None
        self.market_close_message_sent = False
        self.last_market_close_date = None
        self._notification_task: Optional[asyncio.Task] = None

        self._ensure_snapshot_schema()
        
        # Initialize lives tracker (temporarily disabled for deployment)
        # from src.core.lives_tracker import LivesTracker
        # self.lives_tracker = LivesTracker()
        
        # Check life status on startup (temporarily disabled)
        life_status = {"life_number": 1, "health_percentage": 100.0}
        
        logger.info("🎯 Options Trading Scheduler initialized")
        logger.info(f"📊 Mode: {self.trading_mode.get_mode_description()}")
        logger.info(f"💰 Starting balance: ${options_paper_trader.account_balance:.2f}")
        logger.info(f"🎮 Life #{life_status['life_number']} - Health: {life_status['health_percentage']:.1f}%")
    
    async def start_autonomous_trading(self):
        """Start the main autonomous trading loop"""
        
        if self.running:
            logger.warning("⚠️ Scheduler already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 Starting autonomous options trading")
        await notification_center.ensure_started()
        await notification_center.send_message(
            "🚀 **RTX Options Trading Started**\n\n"
            f"Mode: {self.trading_mode.get_mode_description()}\n"
            f"Balance: ${options_paper_trader.account_balance:.2f}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown",
        )
        
        try:
            # Start Telegram listener as background task
            telegram_task = asyncio.create_task(telegram_bot.process_incoming_messages())
            logger.info("📱 Started Telegram command listener")
            self._notification_task = asyncio.create_task(self._notification_watchdog())
            logger.info("📡 Notification watchdog started")
            
            while self.running:
                # Check if market is open
                if not options_config.is_market_hours():
                    logger.info("⏰ Market closed - sleeping")
                    await asyncio.sleep(300)  # Check every 5 minutes
                    continue
                
                # Send market open status message (once per day)
                await self._check_and_send_market_open_status()

                # Check for automated ML notifications
                await self._check_and_send_ml_notification()

                # Send market close summary if applicable
                await self._check_and_send_market_close_status()

                # Run trading cycle
                await self._run_trading_cycle()
                
                # Wait for next cycle (15 minutes)
                await asyncio.sleep(900)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            await notification_center.send_message(f"🚨 **Scheduler Error:** {e}", parse_mode="Markdown")
        finally:
            self.running = False
            # Cancel Telegram listener task
            if 'telegram_task' in locals():
                telegram_task.cancel()
                try:
                    await telegram_task
                except asyncio.CancelledError:
                    pass
            if self._notification_task:
                self._notification_task.cancel()
                try:
                    await self._notification_task
                except asyncio.CancelledError:
                    pass
            logger.info("⏹️ Autonomous trading stopped")
    
    async def _run_trading_cycle(self):
        """Run a complete trading cycle"""
        
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        # Log current balance at start of cycle for tracking
        current_balance = options_paper_trader.account_balance
        logger.info(f"🔄 Starting trading cycle #{self.cycle_count}")
        logger.info(f"💰 Current account balance: ${current_balance:.2f}")
        
        try:
            # Step 0: Check life status (temporarily disabled)
            # current_balance = self.paper_trader.account_balance
            # life_status = self.lives_tracker.check_life_status(current_balance)
            
            # Step 1: Check existing positions
            await self._check_existing_positions()
            
            # Step 2: Track prediction outcomes (every 5th cycle)
            if self.cycle_count % 5 == 0:
                asyncio.create_task(outcome_tracker.track_all_outcomes())
            
            # Step 3: Generate new signals
            signals_data = await self._generate_signals()
            
            if not signals_data:
                logger.warning("⚠️ No signals generated")
                return
            
            # Step 3: Create options prediction
            logger.info("🎯 Creating options prediction from signals...")
            prediction = await self._create_options_prediction(signals_data)
            
            if prediction:
                logger.info(f"📋 Options prediction created: {prediction.get('action', 'UNKNOWN')} confidence={prediction.get('confidence', 0):.1%}")
                # Step 4: Execute trade (if conditions are met)
                await self._execute_options_trade(prediction)
            else:
                logger.warning("⚠️ No options prediction generated - confidence too low or no suitable contracts")
            
            # Step 5: Send status update
            await self._send_cycle_update(signals_data, prediction)
            
        except Exception as e:
            logger.error(f"❌ Trading cycle error: {e}")
            await notification_center.send_message(f"🚨 **Cycle Error:** {e}", parse_mode="Markdown")
        
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        logger.info(f"✅ Trading cycle #{self.cycle_count} completed in {cycle_duration:.1f}s")
    
    async def _check_existing_positions(self):
        """Check and manage existing positions"""
        
        # Always log position status for better tracking
        position_count = len(options_paper_trader.open_positions)
        logger.info(f"📊 Position check: {position_count} open positions")
        
        if not options_paper_trader.open_positions:
            logger.info("📑 No open positions to check")
            return
        
        # Log details of each position
        total_value = 0
        for pos_id, position in options_paper_trader.open_positions.items():
            pos_value = position.get('current_value', 0)
            total_value += pos_value
            pnl = position.get('unrealized_pnl', 0)
            pnl_pct = position.get('unrealized_pnl_pct', 0)
            logger.info(f"  • {position.get('contract_symbol', 'Unknown')}: ${pos_value:.2f} (PnL: ${pnl:.2f}, {pnl_pct:+.1f}%)")
        
        logger.info(f"📊 Total position value: ${total_value:.2f}")
        
        # Check all positions for exit conditions
        actions = options_paper_trader.check_positions()
        
        if actions:
            logger.info(f"🎯 Found {len(actions)} position actions to execute")
            for action in actions:
                logger.info(f"📈 Position action: {action}")
                await notification_center.send_message(f"📈 **Position Update**\n{action}", parse_mode="Markdown")
        else:
            logger.info("✓ All positions within normal parameters")
    
    async def _generate_signals(self) -> Optional[Dict]:
        """Generate and aggregate all AI signals"""
        
        logger.info("🤖 Generating AI signals...")
        
        signal_results = {}
        successful_signals = 0
        
        # Run all signals in parallel for speed
        signal_tasks = []
        
        for signal_name, signal_instance in self.signals.items():
            task = asyncio.create_task(
                self._run_single_signal(signal_name, signal_instance),
                name=signal_name
            )
            signal_tasks.append(task)
        
        # Wait for all signals to complete
        results = await asyncio.gather(*signal_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            signal_name = list(self.signals.keys())[i]
            
            if isinstance(result, Exception):
                logger.error(f"❌ Signal {signal_name} failed: {result}")
                signal_results[signal_name] = {
                    "direction": "HOLD",
                    "confidence": 0.5,
                    "strength": 0.0,
                    "error": str(result)
                }
            else:
                signal_results[signal_name] = result
                if result.get("direction") != "HOLD":
                    successful_signals += 1
        
        if successful_signals == 0:
            logger.warning("⚠️ No actionable signals generated")
            return None
        
        # Aggregate signals using weighted voting
        aggregated = self._aggregate_signals(signal_results)
        
        # DEBUG: Log detailed signal analysis
        logger.info(f"🔍 SIGNAL ANALYSIS DEBUG:")
        logger.info(f"   • Total signals: {len(self.signals)}")
        logger.info(f"   • Successful signals: {successful_signals}")
        logger.info(f"   • Aggregated confidence: {aggregated.get('confidence', 0):.1%}")
        logger.info(f"   • Aggregated direction: {aggregated.get('direction', 'UNKNOWN')}")
        logger.info(f"   • Expected move: {aggregated.get('expected_move_pct', 0):.2%}")
        
        # Log individual signal details
        for name, result in signal_results.items():
            if result and 'confidence' in result:
                conf = result['confidence']
                # Handle confidence as percentage (0-100) vs decimal (0-1)
                if conf > 1:
                    conf_display = f"{conf:.1f}%"
                else:
                    conf_display = f"{conf:.1%}"
                logger.info(f"   • {name}: {result['direction']} ({conf_display})")
        
        logger.success(f"✅ Generated {successful_signals}/{len(self.signals)} actionable signals")
        
        return {
            "individual_signals": signal_results,
            "signal_weights": self.signal_weights,
            "signals_agreeing": successful_signals,
            "total_signals": len(self.signals),
            **aggregated
        }
    
    async def _run_single_signal(self, name: str, signal_instance) -> Dict:
        """Run a single signal with error handling"""
        
        try:
            result = await signal_instance.analyze("RTX")
            
            # Ensure result has required fields
            if not isinstance(result, dict):
                raise ValueError(f"Signal {name} returned invalid format")
            
            result.setdefault("direction", "HOLD")
            result.setdefault("confidence", 0.5)
            result.setdefault("strength", 0.1)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Signal {name} error: {e}")
            return {
                "direction": "HOLD",
                "confidence": 0.5,
                "strength": 0.0,
                "error": str(e)
            }
    
    def _aggregate_signals(self, signal_results: Dict) -> Dict:
        """Enhanced signal aggregation with high-confidence bias"""
        
        buy_signals = []
        sell_signals = []
        high_conf_signals = []
        telemetry_snapshot = []
        
        for signal_name, result in signal_results.items():
            if "error" in result:
                continue
            
            direction = result.get("direction", "HOLD")
            strength = result.get("strength", 0.1)
            confidence = result.get("confidence", 0.5)
            weight = self.signal_weights.get(signal_name, 0.1)
            
            # Convert percentage confidence to decimal if needed
            if confidence > 1:
                confidence = confidence / 100.0
            
            signal_data = {
                'name': signal_name,
                'direction': direction,
                'confidence': confidence,
                'strength': strength,
                'weight': weight,
                'weighted_strength': weight * confidence
            }

            telemetry_snapshot.append(signal_data)

            if direction == "BUY":
                buy_signals.append(signal_data)
            elif direction == "SELL":
                sell_signals.append(signal_data)
                
            # Track high confidence signals (>70%)
            if confidence > 0.7:
                high_conf_signals.append(signal_data)
        
        # Calculate total strengths
        buy_strength = sum(s['weighted_strength'] for s in buy_signals) / max(sum(self.signal_weights.values()), 1.0) if buy_signals else 0
        sell_strength = sum(s['weighted_strength'] for s in sell_signals) / max(sum(self.signal_weights.values()), 1.0) if sell_signals else 0
        
        # Enhanced decision logic
        logger.info(f"🔍 AGGREGATION DEBUG: BUY={buy_strength:.3f}, SELL={sell_strength:.3f}")
        logger.info(f"   High-confidence signals: {len(high_conf_signals)}")
        
        # Check for overwhelming high-confidence signal
        if high_conf_signals:
            strongest_signal = max(high_conf_signals, key=lambda x: x['confidence'] * x['weight'])
            if strongest_signal['confidence'] > 0.85:
                logger.info(f"   🎯 Using strongest signal: {strongest_signal['name']} ({strongest_signal['confidence']:.1%})")
                result = {
                    "direction": strongest_signal['direction'],
                    "confidence": strongest_signal['confidence'] * 0.9,  # Slight discount for safety
                    "expected_move_pct": strongest_signal['strength'] * 0.05,
                    "buy_strength": buy_strength,
                    "sell_strength": sell_strength,
                    "dominant_signal": strongest_signal['name']
                }

                snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'final_direction': result['direction'],
                    'final_confidence': result['confidence'],
                    'buy_strength': buy_strength,
                    'sell_strength': sell_strength,
                    'total_strength': buy_strength + sell_strength,
                    'strength_diff': abs(buy_strength - sell_strength),
                    'signals': telemetry_snapshot,
                }

                try:
                    self._persist_signal_snapshot(snapshot)
                except Exception as exc:
                    logger.warning(f"⚠️ Failed to persist signal snapshot: {exc}")

                return result
        
        # Standard aggregation with lower thresholds
        strength_diff = abs(buy_strength - sell_strength)
        total_strength = buy_strength + sell_strength
        
        # Lower thresholds to allow more trades
        min_strength = 0.15  # Reduced from 0.35
        min_agreement = 0.1   # Reduced from 0.25
        
        if buy_strength > sell_strength and total_strength > min_strength and strength_diff > min_agreement:
            final_direction = "BUY"
            final_confidence = min(0.85, (buy_strength / (total_strength + 0.01)) * 0.8 + 0.5)
        elif sell_strength > buy_strength and total_strength > min_strength and strength_diff > min_agreement:
            final_direction = "SELL" 
            final_confidence = min(0.85, (sell_strength / (total_strength + 0.01)) * 0.8 + 0.5)
        else:
            final_direction = "HOLD"
            final_confidence = 0.5
        
        # Calculate expected move
        expected_move = min(0.06, strength_diff * 0.8)  # More conservative
        
        logger.info(f"   📊 Final: {final_direction} ({final_confidence:.1%})")

        aligned = [sig for sig in telemetry_snapshot if sig['direction'] == final_direction]
        aligned_count = len(aligned)
        aligned_weight = sum(sig['weight'] for sig in aligned)

        result = {
            "direction": final_direction,
            "confidence": final_confidence,
            "expected_move_pct": expected_move,
            "buy_strength": buy_strength,
            "sell_strength": sell_strength,
            "aligned_count": aligned_count,
            "aligned_weight": aligned_weight,
        }

        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'final_direction': result['direction'],
            'final_confidence': result['confidence'],
            'buy_strength': buy_strength,
            'sell_strength': sell_strength,
            'total_strength': total_strength,
            'strength_diff': strength_diff,
            'aligned_count': aligned_count,
            'aligned_weight': aligned_weight,
            'signals': telemetry_snapshot,
        }

        try:
            self._persist_signal_snapshot(snapshot)
        except Exception as exc:
            logger.warning(f"⚠️ Failed to persist signal snapshot: {exc}")

        return result
    

    def _adjust_weights_for_regime(self, base_weights: Dict, regime_type: str) -> Dict:
        """Adjust signal weights based on market regime"""
        adjusted = base_weights.copy()
        
        if regime_type == "trending":
            # Boost momentum and technical signals in trending markets
            adjusted["momentum"] = min(adjusted.get("momentum", 0.08) * 1.3, 0.15)
            adjusted["technical_analysis"] = min(adjusted.get("technical_analysis", 0.12) * 1.2, 0.18)
            # Reduce mean reversion in trending markets
            adjusted["mean_reversion"] = adjusted.get("mean_reversion", 0.08) * 0.7
        else:  # ranging market
            # Boost mean reversion in ranging markets
            adjusted["mean_reversion"] = min(adjusted.get("mean_reversion", 0.08) * 1.4, 0.15)
            # Reduce momentum in ranging markets
            adjusted["momentum"] = adjusted.get("momentum", 0.08) * 0.8
            
        # Normalize weights to sum to 1.0
        total = sum(adjusted.values())
        return {k: v/total for k, v in adjusted.items()}


    def _adjust_weights_for_regime(self, base_weights: Dict, regime_type: str) -> Dict:
        """Adjust signal weights based on market regime"""
        adjusted = base_weights.copy()
        
        if regime_type == "trending":
            # Boost momentum and technical signals in trending markets
            adjusted["momentum"] = min(adjusted.get("momentum", 0.08) * 1.3, 0.15)
            adjusted["technical_analysis"] = min(adjusted.get("technical_analysis", 0.12) * 1.2, 0.18)
            # Reduce mean reversion in trending markets
            adjusted["mean_reversion"] = adjusted.get("mean_reversion", 0.08) * 0.7
        else:  # ranging market
            # Boost mean reversion in ranging markets
            adjusted["mean_reversion"] = min(adjusted.get("mean_reversion", 0.08) * 1.4, 0.15)
            # Reduce momentum in ranging markets
            adjusted["momentum"] = adjusted.get("momentum", 0.08) * 0.8
            
        # Normalize weights to sum to 1.0
        total = sum(adjusted.values())
        return {k: v/total for k, v in adjusted.items()}

    async def _create_options_prediction(self, signals_data: Dict) -> Optional[Dict]:
        """Create options-specific prediction"""
        
        if signals_data.get("direction", "HOLD") == "HOLD":
            return None

        current_confidence = signals_data.get("confidence", 0.5)
        logger.info(f"📊 Evaluating options prediction with confidence {current_confidence:.3f}")

        min_confidence = getattr(options_config, 'MIN_CONFIDENCE', 0.65)

        if current_confidence < min_confidence:
            logger.info(f"📊 Confidence {current_confidence:.1%} below {min_confidence:.1%} options threshold")
            return None

        # Generate options prediction
        prediction = options_prediction_engine.generate_options_prediction(
            signals_data,
            options_paper_trader.account_balance,
            strategy_id=getattr(self, 'strategy_id', 'options_single')
        )
        
        if prediction:
            self.last_options_prediction = prediction
            self.prediction_count += 1
            
            # Track signal effectiveness for this prediction
            prediction_id = prediction.get('prediction_id', f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Extract individual signal data from signals_data
            individual_signals = {}
            for signal_name in self.signal_weights.keys():
                if signal_name in signals_data.get('signals', {}):
                    signal_info = signals_data['signals'][signal_name]
                    individual_signals[signal_name] = {
                        'confidence': signal_info.get('confidence', 0.0),
                        'direction': signal_info.get('direction', signals_data.get('direction', 'UNKNOWN'))
                    }
            
            # Track signals for this prediction (with strategy-specific ID)
            strategy_id = getattr(self, 'strategy_id', 'options_single')
            signal_tracker.track_prediction_signals(
                prediction_id, 
                individual_signals, 
                strategy_id=strategy_id
            )
            
            logger.success(f"🎯 Options prediction #{self.prediction_count}: {prediction['action']}")
            logger.debug(f"📊 Tracked {len(individual_signals)} signals for prediction {prediction_id}")
        
        return prediction
    
    async def _execute_options_trade(self, prediction: Dict):
        """Execute options trade based on prediction"""
        
        if not self.trading_mode.TRADING_ENABLED:
            logger.info("📊 Trading disabled - prediction only mode")
            return
        
        # Check if we should limit position count
        max_positions = 8  # Increased from 3 to allow more trades
        current_positions = len(options_paper_trader.open_positions)
        
        if current_positions >= max_positions:
            logger.info(f"📊 Maximum positions reached ({current_positions}/{max_positions}) - skipping trade")
            return
        else:
            logger.info(f"📊 Position count: {current_positions}/{max_positions} - proceeding with trade evaluation")
        
        # Execute the trade
        success = options_paper_trader.open_position(prediction)
        
        if success:
            await notification_center.send_message(
                f"🎯 **OPTIONS TRADE EXECUTED**\n\n"
                f"📊 **Contract Details:**\n"
                f"• Action: {prediction['action']}\n"
                f"• Contract: {prediction['contract_symbol']}\n"
                f"• Type: {prediction['option_type'].upper()}\n"
                f"• Strike: ${prediction['strike']}\n"
                f"• Expiry: {prediction['expiry']} ({prediction['days_to_expiry']}d)\n\n"
                f"💰 **Trade Details:**\n"
                f"• Contracts: {prediction['contracts']}x\n"
                f"• Entry Price: ${prediction['entry_price']:.2f} (Ask)\n"
                f"• Total Cost: ${prediction['total_cost']:.2f}\n"
                f"• Commission: ${prediction['commission']:.2f}\n\n"
                f"📈 **Greeks & Analytics:**\n"
                f"• Delta: {prediction['delta']:.3f}\n"
                f"• IV: {prediction['implied_volatility']*100:.1f}%\n"
                f"• Confidence: {prediction['confidence']:.1%}\n"
                f"• Expected Profit: {prediction['expected_profit_pct']:.1f}%\n\n"
                f"🎯 **Exit Strategy:**\n"
                f"• Target: ${prediction['profit_target_price']:.2f} (+100%)\n"
                f"• Stop Loss: ${prediction['stop_loss_price']:.2f} (-50%)\n"
                f"• Time Exit: {prediction['exit_before_expiry_days']}d before expiry",
                parse_mode="Markdown",
            )
        else:
            await notification_center.send_message(
                f"❌ **Trade Failed**\n\n"
                f"Could not execute: {prediction['contract_symbol']}",
                parse_mode="Markdown",
            )
    
    async def _send_cycle_update(self, signals_data: Dict, prediction: Optional[Dict]):
        """Send cycle status update"""
        
        # Only send updates every 4 cycles (hourly) to avoid spam
        if self.cycle_count % 4 != 0:
            return
        
        # Get performance summary
        performance = options_paper_trader.get_performance_summary()
        open_positions = options_paper_trader.get_open_positions_summary()
        
        message = f"📊 **Hourly Update #{self.cycle_count // 4}**\n\n"
        
        # Account status
        message += f"💰 **Account**: ${performance['account_balance']:.2f} "
        message += f"({performance['total_return']:+.2f}, {performance['total_return_pct']:+.1%})\n\n"
        
        # Current prediction
        if prediction:
            message += f"🎯 **Latest Signal**: {prediction['action']} "
            message += f"{prediction['contract_symbol']} ({prediction['confidence']:.1%})\n\n"
        else:
            direction = signals_data.get('direction', 'HOLD')
            confidence = signals_data.get('confidence', 0.5)
            message += f"🎯 **Latest Signal**: {direction} "
            message += f"({confidence:.1%}) - No options trade\n\n"
        
        # Open positions
        if open_positions:
            message += f"📈 **Open Positions** ({len(open_positions)}):  \n"
            for pos in open_positions[:3]:  # Show up to 3
                pnl_emoji = "💰" if pos['unrealized_pnl'] > 0 else "💸"
                message += f"{pnl_emoji} {pos['contract_symbol']}: {pos['unrealized_pnl']:+.0f} ({pos['unrealized_pnl_pct']:+.1f}%)\n"
            message += "\n"
        
        # Performance stats
        if performance['total_trades'] > 0:
            message += f"📊 **Performance**: {performance['win_rate']:.1f}% win rate, "
            message += f"{performance['total_trades']} trades, "
            message += f"PF: {performance['profit_factor']:.1f}"
        
        await notification_center.send_message(message, parse_mode="Markdown")
    
    async def _notification_watchdog(self):
        """Ensure heartbeat notifications fire even if trading loop starts late."""
        try:
            while self.running:
                await self._check_and_send_market_open_status(via_watchdog=True)
                await self._check_and_send_market_close_status(via_watchdog=True)
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.debug("🔕 Notification watchdog cancelled")
        except Exception as exc:
            logger.error(f"❌ Notification watchdog error: {exc}")

    async def _check_and_send_market_open_status(self, via_watchdog: bool = False):
        """Check if we should send the daily market open status message"""
        try:
            # Get current date in ET timezone
            import pytz
            et = pytz.timezone('US/Eastern')
            now = datetime.now(et)
            current_date = now.date()
            current_time = now.time()
            
            # Skip weekends but reset flags so Monday triggers correctly
            if now.weekday() >= 5:
                self.last_market_open_date = current_date
                self.market_open_message_sent = False
                return
            
            if self.last_market_open_date != current_date:
                self.market_open_message_sent = False
            
            if self.market_open_message_sent:
                return
            
            # Only start sending after market open
            if current_time < dt_time(9, 30):
                return
            
            # Determine if we're late so we can annotate the message
            late_note = None
            if current_time >= dt_time(16, 0):
                late_note = "Service restarted after market close; sending open status retroactively."
            elif current_time > dt_time(10, 0):
                late_note = "Service started after the usual notification window; sending status now."
            elif via_watchdog:
                # Normal window triggered by watchdog
                late_note = None
            
            logger.info("📱 Sending daily market open status message...")
            summary = self._build_previous_day_summary(current_date)
            success = await notification_center.send_market_open_status(summary, note=late_note)
            
            if success:
                self.market_open_message_sent = True
                self.last_market_open_date = current_date
                logger.success("✅ Market open status message sent successfully")
            else:
                logger.error("❌ Failed to send market open status message")
                
        except Exception as e:
            logger.error(f"❌ Error checking market open status: {e}")
    
    async def _check_and_send_ml_notification(self):
        """Check if we should send automated ML status notification"""
        try:
            # Send automated ML notification if conditions are met
            await notification_center.send_automated_ml_notification()
            
        except Exception as e:
            logger.error(f"❌ Error checking ML notification: {e}")

    async def _check_and_send_market_close_status(self, via_watchdog: bool = False):
        try:
            import pytz

            et = pytz.timezone('US/Eastern')
            now = datetime.now(et)
            current_date = now.date()

            if self.last_market_close_date != current_date:
                self.market_close_message_sent = False

            if self.market_close_message_sent:
                return

            if now.weekday() >= 5:
                self.last_market_close_date = current_date
                self.market_close_message_sent = False
                return

            if now.time() < dt_time(16, 0):
                return

            late_note = None
            if now.time() > dt_time(17, 0):
                late_note = "Service resumed after the scheduled close window; summary sent late."

            summary = self._build_daily_summary(current_date)
            open_positions = []
            for pos in options_paper_trader.open_positions.values():
                open_positions.append({
                    'contract_symbol': pos.get('contract_symbol', 'N/A'),
                    'entry_price': pos.get('entry_price', 0.0),
                    'confidence': pos.get('confidence', 0.0),
                })
            success = await notification_center.send_market_close_summary(summary, open_positions, note=late_note)
            if success:
                self.market_close_message_sent = True
                self.last_market_close_date = current_date
                logger.success("✅ Market close summary sent")

        except Exception as e:
            logger.error(f"❌ Error sending market close summary: {e}")

    def _persist_signal_snapshot(self, snapshot: Dict) -> None:
        """Persist aggregation snapshot to SQLite for later analysis."""
        import sqlite3
        import json

        conn = sqlite3.connect(self.telemetry_db)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS signal_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                final_direction TEXT,
                final_confidence REAL,
                buy_strength REAL,
                sell_strength REAL,
                total_strength REAL,
                strength_diff REAL,
                aligned_count INTEGER,
                aligned_weight REAL,
                signals_json TEXT
            )
            """
        )

        # Ensure new columns exist for backward compatibility
        try:
            conn.execute("ALTER TABLE signal_snapshots ADD COLUMN aligned_count INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE signal_snapshots ADD COLUMN aligned_weight REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            INSERT INTO signal_snapshots (
                timestamp, final_direction, final_confidence,
                buy_strength, sell_strength, total_strength,
                strength_diff, aligned_count, aligned_weight, signals_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot['timestamp'],
                snapshot['final_direction'],
                snapshot['final_confidence'],
                snapshot['buy_strength'],
                snapshot['sell_strength'],
                snapshot['total_strength'],
                snapshot['strength_diff'],
                snapshot.get('aligned_count', 0),
                snapshot.get('aligned_weight', 0.0),
                json.dumps(snapshot['signals']),
            ),
        )

        conn.commit()
        conn.close()

    def _build_daily_summary(self, target_date: date) -> Dict:
        summary = {
            'date': target_date,
            'signal_count': 0,
            'buy_count': 0,
            'sell_count': 0,
            'hold_count': 0,
            'avg_confidence': 0.0,
            'avg_buy_strength': 0.0,
            'avg_sell_strength': 0.0,
            'avg_aligned_weight': 0.0,
            'top_signals': [],
            'predictions': 0,
            'prediction_status': {},
        }

        conn = sqlite3.connect(self.telemetry_db)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT final_direction, final_confidence, buy_strength, sell_strength,
                   aligned_weight, signals_json
            FROM signal_snapshots
            WHERE DATE(timestamp) = ?
            """,
            (target_date.isoformat(),)
        )
        rows = cur.fetchall()

        summary['signal_count'] = len(rows)
        signal_contributors = {}

        for direction, confidence, buy_strength, sell_strength, aligned_weight, signals_json in rows:
            summary['avg_confidence'] += confidence
            summary['avg_buy_strength'] += buy_strength
            summary['avg_sell_strength'] += sell_strength
            summary['avg_aligned_weight'] += aligned_weight

            match direction:
                case 'BUY':
                    summary['buy_count'] += 1
                case 'SELL':
                    summary['sell_count'] += 1
                case _:
                    summary['hold_count'] += 1

            try:
                signals = json.loads(signals_json)
            except Exception:
                signals = []

            for sig in signals:
                name = sig.get('name')
                if not name:
                    continue
                signal_contributors.setdefault(name, 0)
                if sig.get('direction') == direction:
                    signal_contributors[name] += 1

        if rows:
            count = len(rows)
            summary['avg_confidence'] /= count
            summary['avg_buy_strength'] /= count
            summary['avg_sell_strength'] /= count
            summary['avg_aligned_weight'] /= count

        summary['top_signals'] = sorted(signal_contributors.items(), key=lambda x: x[1], reverse=True)[:3]

        cur.execute(
            """
            SELECT status, COUNT(*) FROM options_predictions
            WHERE DATE(timestamp) = ?
            GROUP BY status
            """,
            (target_date.isoformat(),)
        )
        for status, count in cur.fetchall():
            summary['prediction_status'][status or 'UNKNOWN'] = count
            summary['predictions'] += count

        try:
            cur.execute("SELECT balance_after FROM account_history ORDER BY rowid DESC LIMIT 1")
            row = cur.fetchone()
            if row:
                summary['balance'] = row[0]
        except Exception:
            summary['balance'] = None

        conn.close()
        return summary

    def _build_previous_day_summary(self, current_date: date) -> Optional[Dict]:
        for offset in range(1, 6):
            candidate = current_date - timedelta(days=offset)
            stats = self._build_daily_summary(candidate)
            if stats['signal_count'] or stats['predictions']:
                return stats
        return None

    def _ensure_snapshot_schema(self) -> None:
        conn = sqlite3.connect(self.telemetry_db)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(signal_snapshots)")
        columns = {row[1] for row in cur.fetchall()}

        if 'aligned_count' not in columns:
            cur.execute("ALTER TABLE signal_snapshots ADD COLUMN aligned_count INTEGER DEFAULT 0")
        if 'aligned_weight' not in columns:
            cur.execute("ALTER TABLE signal_snapshots ADD COLUMN aligned_weight REAL DEFAULT 0")

        conn.commit()
        conn.close()

    def stop(self):
        """Stop the trading scheduler"""
        self.running = False
        logger.info("⏹️ Stop signal sent to scheduler")
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "running": self.running,
            "uptime_seconds": uptime,
            "cycle_count": self.cycle_count,
            "prediction_count": self.prediction_count,
            "last_prediction": self.last_options_prediction,
            "open_positions": len(options_paper_trader.open_positions),
            "account_balance": options_paper_trader.account_balance,
            "performance": options_paper_trader.get_performance_summary()
        }

# Create global instance
options_scheduler = OptionsScheduler()

if __name__ == "__main__":
    # Test the scheduler
    logger.info("🧪 Testing Options Scheduler...")
    
    async def test_scheduler():
        scheduler = OptionsScheduler()
        
        # Test signal generation
        signals = await scheduler._generate_signals()
        if signals:
            print(f"Generated signals: {signals['direction']} ({signals['confidence']:.1%})")
            
            # Test prediction creation
            prediction = await scheduler._create_options_prediction(signals)
            if prediction:
                print(f"Generated prediction: {prediction['contract_symbol']}")
    
    asyncio.run(test_scheduler())
