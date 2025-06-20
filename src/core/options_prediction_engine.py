"""
Options Prediction Engine
Converts AI signals into specific options trade recommendations
Predicts exact option contracts, entry prices, and profit targets
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger

from config.options_config import options_config
from src.core.options_data_engine import options_data_engine

class OptionsPredictionEngine:
    """Converts AI signals into actionable options predictions"""
    
    def __init__(self):
        self.last_prediction = None
        self.prediction_history = []
    
    def generate_options_prediction(self, signals_data: Dict, account_balance: float, strategy_id: str = "default") -> Optional[Dict]:
        """
        Generate specific options prediction from AI signals
        
        Args:
            signals_data: Output from signal fusion system
            account_balance: Current account balance for position sizing
            
        Returns:
            Specific options trade prediction with all details
        """
        
        if not options_config.is_market_hours():
            logger.info("⏰ Market closed - no options predictions")
            return None
        
        # Extract signal information
        direction = signals_data.get('direction', 'HOLD')
        confidence = signals_data.get('confidence', 0.5)
        expected_move = signals_data.get('expected_move', 0.0)
        signals_agreeing = signals_data.get('signals_agreeing', 0)
        
        # Minimum confidence threshold for options trading
        min_confidence = 0.75  # Higher than stock trading
        if confidence < min_confidence:
            logger.info(f"📊 Confidence {confidence:.1%} below {min_confidence:.1%} threshold")
            return None
        
        if direction == "HOLD":
            logger.info("📊 No directional signal - holding")
            return None
        
        logger.info(f"🎯 Generating options prediction: {direction} with {confidence:.1%} confidence")
        
        # Get best option candidates
        best_options = options_data_engine.get_best_options_for_direction(
            direction, confidence, account_balance
        )
        
        if not best_options:
            logger.warning("❌ No suitable options found")
            return None
        
        # Select the best option
        selected_option = self._select_optimal_option(best_options, confidence, expected_move)
        
        if not selected_option:
            logger.warning("❌ No optimal option selected")
            return None
        
        # Generate complete prediction
        prediction = self._create_options_prediction(
            selected_option, direction, confidence, expected_move, 
            signals_data, account_balance, strategy_id
        )
        
        # Validate prediction
        if not self._validate_prediction(prediction):
            logger.error("❌ Prediction failed validation")
            return None
        
        # Store prediction
        self.last_prediction = prediction
        self.prediction_history.append(prediction)
        
        logger.success(f"✅ Options prediction: {prediction['action']} {prediction['contract_symbol']} @ ${prediction['entry_price']:.2f}")
        
        return prediction
    
    def _select_optimal_option(self, candidates: List[Dict], confidence: float, expected_move: float) -> Optional[Dict]:
        """Select the most optimal option from candidates"""
        
        if not candidates:
            return None
        
        # Score each candidate
        scored_options = []
        
        for option in candidates:
            score = self._calculate_option_attractiveness(option, confidence, expected_move)
            scored_options.append((score, option))
        
        # Sort by score (highest first)
        scored_options.sort(key=lambda x: x[0], reverse=True)
        
        # Return the best option
        return scored_options[0][1] if scored_options else None
    
    def _calculate_option_attractiveness(self, option: Dict, confidence: float, expected_move: float) -> float:
        """Calculate how attractive an option is for our prediction"""
        
        score = 0.0
        
        # Liquidity Score (25%)
        volume_score = min(option['volume'] / 500, 1.0) * 0.15
        oi_score = min(option['openInterest'] / 2000, 1.0) * 0.10
        
        # Pricing Score (25%)
        spread_score = max(0, (0.15 - option['spread_pct']) / 0.15) * 0.15
        price_score = 0.10 if 0.50 <= option['mid_price'] <= 8.0 else 0.05
        
        # Greeks Score (30%)
        delta = abs(option.get('delta', 0))
        gamma = option.get('gamma', 0)
        theta = abs(option.get('theta', 0))
        
        # Higher delta for high confidence predictions
        delta_score = (delta * confidence) * 0.15
        
        # Positive gamma (acceleration)
        gamma_score = min(gamma * 1000, 0.10) * 0.10
        
        # Lower theta decay is better for long options
        theta_score = max(0, (0.10 - theta) / 0.10) * 0.05
        
        # Expected Move Alignment (20%)
        # Check if option strike aligns with expected move
        stock_price = options_data_engine.get_current_stock_price()
        if stock_price:
            strike = option['strike']
            
            if option['type'] == 'call':
                # For calls, we want the strike below target price
                target_price = stock_price * (1 + expected_move)
                strike_alignment = max(0, min(1, (target_price - strike) / stock_price)) * 0.20
            else:
                # For puts, we want the strike above target price
                target_price = stock_price * (1 - expected_move)
                strike_alignment = max(0, min(1, (strike - target_price) / stock_price)) * 0.20
            
            score += strike_alignment
        
        return volume_score + oi_score + spread_score + price_score + delta_score + gamma_score + theta_score
    
    def _create_options_prediction(self, option: Dict, direction: str, confidence: float, 
                                 expected_move: float, signals_data: Dict, account_balance: float, strategy_id: str = "default") -> Dict:
        """Create complete options prediction with all details"""
        
        # Determine action
        if direction == "BUY" and option['type'] == 'call':
            action = "BUY_TO_OPEN_CALL"
        elif direction == "SELL" and option['type'] == 'put':
            action = "BUY_TO_OPEN_PUT"
        else:
            action = "HOLD"
        
        # Calculate position sizing
        entry_price = option['ask']  # We'll pay the ask price
        max_contracts = option['max_contracts']
        position_size = options_config.get_position_size(account_balance)
        
        # Calculate costs
        cost_per_contract = entry_price * 100
        total_cost_before_commission = cost_per_contract * max_contracts
        commission = options_config.calculate_commission(action, max_contracts)
        total_cost = total_cost_before_commission + commission
        
        # Calculate profit targets and stop loss
        profit_target_price = entry_price * (1 + options_config.PROFIT_TARGET_PCT)
        stop_loss_price = entry_price * (1 - options_config.STOP_LOSS_PCT)
        
        # Calculate days to expiration
        exp_date = datetime.strptime(option['expiry'], "%Y-%m-%d")
        days_to_expiry = (exp_date - datetime.now()).days
        
        # Exit strategy
        exit_before_expiry = max(1, days_to_expiry // 4)  # Exit when 25% of time remains
        
        # Expected profit calculation
        if expected_move > 0:
            # Rough estimate: options can provide 3-5x leverage on stock moves
            leverage_factor = 3 + (confidence * 2)  # 3x to 5x based on confidence
            expected_profit_pct = expected_move * leverage_factor
        else:
            expected_profit_pct = options_config.PROFIT_TARGET_PCT * confidence
        
        prediction = {
            # Basic Trade Information
            'timestamp': datetime.now().isoformat(),
            'symbol': 'RTX',
            'action': action,
            'contract_symbol': option['contract_symbol'],
            'option_type': option['type'],
            'strike': option['strike'],
            'expiry': option['expiry'],
            'days_to_expiry': days_to_expiry,
            
            # Pricing Information
            'entry_price': entry_price,
            'bid': option['bid'],
            'ask': option['ask'],
            'mid_price': option['mid_price'],
            'spread_pct': option['spread_pct'],
            
            # Position Sizing
            'contracts': max_contracts,
            'cost_per_contract': cost_per_contract,
            'total_cost': total_cost,
            'commission': commission,
            'position_size_pct': total_cost / account_balance,
            
            # Risk Management
            'profit_target_price': profit_target_price,
            'stop_loss_price': stop_loss_price,
            'max_loss_dollars': cost_per_contract * max_contracts * options_config.STOP_LOSS_PCT,
            'max_profit_potential': cost_per_contract * max_contracts * options_config.PROFIT_TARGET_PCT,
            
            # Greeks and IV
            'implied_volatility': option['impliedVolatility'],
            'delta': option.get('delta', 0),
            'gamma': option.get('gamma', 0),
            'theta': option.get('theta', 0),
            'vega': option.get('vega', 0),
            
            # Prediction Details
            'direction': direction,
            'confidence': confidence,
            'expected_move': expected_move,
            'expected_profit_pct': expected_profit_pct,
            'signals_agreeing': signals_data.get('signals_agreeing', 0),
            'total_signals': signals_data.get('total_signals', 0),
            
            # Exit Strategy
            'exit_before_expiry_days': exit_before_expiry,
            'auto_exit_conditions': {
                'profit_target': options_config.PROFIT_TARGET_PCT,
                'stop_loss': options_config.STOP_LOSS_PCT,
                'time_decay': exit_before_expiry
            },
            
            # Liquidity Metrics
            'volume': option['volume'],
            'open_interest': option['openInterest'],
            'liquidity_score': min(option['volume'] / 100, 1.0) + min(option['openInterest'] / 1000, 1.0),
            
            # Signals Data (for learning)
            'individual_signals': signals_data.get('individual_signals', {}),
            'signal_weights': signals_data.get('signal_weights', {}),
            
            # Metadata
            'prediction_id': f"RTX_{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'account_balance': account_balance,
            'market_hours': options_config.is_market_hours(),
            'reasoning': self._generate_reasoning(option, direction, confidence, expected_move)
        }
        
        return prediction
    
    def _generate_reasoning(self, option: Dict, direction: str, confidence: float, expected_move: float) -> str:
        """Generate human-readable reasoning for the prediction"""
        
        stock_price = options_data_engine.get_current_stock_price() or 0
        
        reasoning_parts = [
            f"High confidence {direction} signal ({confidence:.1%})",
            f"Expected move: {expected_move:.1%}",
            f"Strike ${option['strike']:.2f} vs stock ${stock_price:.2f}",
            f"IV: {option['impliedVolatility']:.1f}%",
            f"Volume: {option['volume']}, OI: {option['openInterest']}",
            f"{option.get('days_to_expiry', 0)} days to expiry"
        ]
        
        if option.get('delta'):
            reasoning_parts.append(f"Delta: {option['delta']:.2f}")
        
        return " | ".join(reasoning_parts)
    
    def _validate_prediction(self, prediction: Dict) -> bool:
        """Final validation before returning prediction"""
        
        try:
            # Basic validation
            if not prediction.get('contract_symbol'):
                return False
            
            if prediction.get('total_cost', 0) <= 0:
                return False
            
            if prediction.get('contracts', 0) <= 0:
                return False
            
            # Affordability check
            account_balance = prediction.get('account_balance', 0)
            if prediction['total_cost'] > account_balance:
                logger.error(f"❌ Trade costs ${prediction['total_cost']:.2f} but account has ${account_balance:.2f}")
                return False
            
            # Position size check
            max_position_pct = options_config.MAX_POSITION_SIZE_PCT
            if prediction['position_size_pct'] > max_position_pct:
                logger.error(f"❌ Position size {prediction['position_size_pct']:.1%} exceeds {max_position_pct:.1%} limit")
                return False
            
            # Reasonableness checks
            if prediction['entry_price'] < 0.05:  # Too cheap
                return False
            
            if prediction['entry_price'] > 50:  # Too expensive for our budget
                return False
            
            if prediction['days_to_expiry'] < options_config.MIN_DAYS_TO_EXPIRY:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return False
    
    def get_prediction_summary(self, prediction: Dict) -> str:
        """Generate a concise summary of the prediction"""
        
        if not prediction:
            return "No prediction available"
        
        return (
            f"🎯 {prediction['action']}: {prediction['contract_symbol']} "
            f"@ ${prediction['entry_price']:.2f} x{prediction['contracts']} contracts "
            f"(${prediction['total_cost']:.0f} total, {prediction['confidence']:.1%} confidence)"
        )
    
    def get_recent_predictions(self, limit: int = 5) -> List[Dict]:
        """Get recent predictions for analysis"""
        return self.prediction_history[-limit:] if self.prediction_history else []

# Create global instance
options_prediction_engine = OptionsPredictionEngine()

if __name__ == "__main__":
    # Test the options prediction engine
    logger.info("🧪 Testing Options Prediction Engine...")
    
    # Mock signals data
    test_signals = {
        'direction': 'BUY',
        'confidence': 0.85,
        'expected_move': 0.03,
        'signals_agreeing': 6,
        'total_signals': 8,
        'individual_signals': {
            'technical_analysis': {'direction': 'BUY', 'confidence': 0.8},
            'momentum': {'direction': 'BUY', 'confidence': 0.75}
        }
    }
    
    engine = OptionsPredictionEngine()
    prediction = engine.generate_options_prediction(test_signals, 1000)
    
    if prediction:
        print("✅ Prediction generated successfully!")
        print(f"Contract: {prediction['contract_symbol']}")
        print(f"Entry: ${prediction['entry_price']:.2f}")
        print(f"Total Cost: ${prediction['total_cost']:.2f}")
        print(f"Expected Profit: {prediction['expected_profit_pct']:.1%}")
        print(f"Reasoning: {prediction['reasoning']}")
    else:
        print("❌ No prediction generated")