"""
Options Paper Trading Simulator
Simulates real options trading with commission and slippage
Tracks P&L for learning system with 100% realistic execution
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger

from config.options_config import options_config
from src.core.options_data_engine import options_data_engine

class OptionsPaperTrader:
    """Realistic options paper trading simulation"""
    
    def __init__(self, db_path: str = "data/options_performance.db"):
        self.db_path = db_path
        self.open_positions = {}
        self.closed_positions = []
        self.account_balance = 1000.0  # Starting with $1000
        self.total_pnl = 0.0
        self._init_database()
    
    def _init_database(self):
        """Initialize options trading database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Options predictions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS options_predictions (
            prediction_id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT DEFAULT 'RTX',
            action TEXT NOT NULL,
            contract_symbol TEXT NOT NULL,
            option_type TEXT NOT NULL,
            strike REAL NOT NULL,
            expiry DATE NOT NULL,
            days_to_expiry INTEGER,
            
            -- Entry Details
            entry_price REAL NOT NULL,
            contracts INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            commission REAL NOT NULL,
            
            -- Prediction Details
            direction TEXT NOT NULL,
            confidence REAL NOT NULL,
            expected_move REAL,
            expected_profit_pct REAL,
            
            -- Greeks and IV
            implied_volatility REAL,
            delta_entry REAL,
            gamma_entry REAL,
            theta_entry REAL,
            vega_entry REAL,
            
            -- Risk Management
            profit_target_price REAL,
            stop_loss_price REAL,
            max_loss_dollars REAL,
            
            -- Market Data
            stock_price_entry REAL,
            volume INTEGER,
            open_interest INTEGER,
            
            -- Signals Data
            signals_data TEXT,
            reasoning TEXT,
            
            -- Status
            status TEXT DEFAULT 'OPEN',
            account_balance_at_entry REAL
        )
        """)
        
        # Options outcomes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS options_outcomes (
            outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id TEXT,
            
            -- Exit Details
            exit_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            exit_price REAL,
            exit_reason TEXT,
            days_held INTEGER,
            
            -- P&L Calculation
            entry_cost REAL,
            exit_proceeds REAL,
            gross_pnl REAL,
            commissions_total REAL,
            net_pnl REAL,
            pnl_percentage REAL,
            
            -- Greeks at Exit
            delta_exit REAL,
            implied_volatility_exit REAL,
            
            -- Market Data
            stock_price_exit REAL,
            stock_move_pct REAL,
            
            -- Learning Metrics
            prediction_accuracy REAL,
            actual_vs_expected_move REAL,
            iv_change REAL,
            
            FOREIGN KEY (prediction_id) REFERENCES options_predictions(prediction_id)
        )
        """)
        
        # Account history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            trade_id TEXT,
            amount REAL,
            balance_before REAL,
            balance_after REAL,
            description TEXT
        )
        """)
        
        conn.commit()
        conn.close()
        logger.info("📊 Options paper trading database initialized")
    
    def open_position(self, prediction: Dict) -> bool:
        """Open a new options position based on prediction"""
        
        prediction_id = prediction['prediction_id']
        
        # Check if we can afford this trade
        if prediction['total_cost'] > self.account_balance:
            logger.error(f"❌ Insufficient funds: ${self.account_balance:.2f} < ${prediction['total_cost']:.2f}")
            return False
        
        # Simulate realistic execution
        execution_result = self._simulate_execution(prediction, 'OPEN')
        
        if not execution_result:
            logger.error("❌ Failed to execute trade")
            return False
        
        # Update account balance
        old_balance = self.account_balance
        self.account_balance -= execution_result['total_cost']
        
        # Store position
        position = {
            'prediction': prediction,
            'execution': execution_result,
            'entry_timestamp': datetime.now(),
            'status': 'OPEN'
        }
        
        self.open_positions[prediction_id] = position
        
        # Store in database
        self._store_prediction(prediction, execution_result)
        self._record_account_transaction(
            'OPEN_POSITION', prediction_id, -execution_result['total_cost'],
            old_balance, self.account_balance,
            f"Opened {prediction['contract_symbol']} x{prediction['contracts']}"
        )
        
        logger.success(
            f"✅ Opened position: {prediction['contract_symbol']} x{prediction['contracts']} "
            f"@ ${execution_result['execution_price']:.2f} (Total: ${execution_result['total_cost']:.2f})"
        )
        
        return True
    
    def _simulate_execution(self, prediction: Dict, action: str) -> Optional[Dict]:
        """Simulate realistic order execution with slippage and timing"""
        
        try:
            # Get current option price
            current_data = options_data_engine.get_option_price_realtime(prediction['contract_symbol'])
            
            if not current_data:
                logger.error(f"❌ Cannot get current price for {prediction['contract_symbol']}")
                return None
            
            if action == 'OPEN':
                # We pay the ask price (market order)
                execution_price = current_data['ask']
                
                # Add slippage for larger orders
                contracts = prediction['contracts']
                if contracts > 5:
                    slippage = 0.02 * execution_price  # 2% slippage
                    execution_price += slippage
                    logger.info(f"📊 Applied slippage: +${slippage:.2f}")
                
            else:  # CLOSE
                # We get the bid price (market order)
                execution_price = current_data['bid']
                
                # Subtract slippage for larger orders
                contracts = prediction['contracts']
                if contracts > 5:
                    slippage = 0.02 * execution_price  # 2% slippage
                    execution_price -= slippage
                    logger.info(f"📊 Applied slippage: -${slippage:.2f}")
            
            # Calculate costs
            cost_per_contract = execution_price * 100
            gross_cost = cost_per_contract * prediction['contracts']
            commission = options_config.calculate_commission(action, prediction['contracts'])
            total_cost = gross_cost + commission
            
            return {
                'execution_price': execution_price,
                'cost_per_contract': cost_per_contract,
                'gross_cost': gross_cost,
                'commission': commission,
                'total_cost': total_cost,
                'timestamp': datetime.now(),
                'current_bid': current_data['bid'],
                'current_ask': current_data['ask'],
                'slippage_applied': contracts > 5
            }
            
        except Exception as e:
            logger.error(f"❌ Execution simulation failed: {e}")
            return None
    
    def check_positions(self) -> List[str]:
        """Check all open positions for exit conditions"""
        
        if not self.open_positions:
            return []
        
        actions_taken = []
        
        for prediction_id, position in list(self.open_positions.items()):
            action = self._check_exit_conditions(position)
            
            if action:
                success = self.close_position(prediction_id, action)
                if success:
                    actions_taken.append(f"Closed {prediction_id}: {action}")
        
        return actions_taken
    
    def _check_exit_conditions(self, position: Dict) -> Optional[str]:
        """Check if position should be closed"""
        
        prediction = position['prediction']
        entry_timestamp = position['entry_timestamp']
        
        # Get current option price
        current_data = options_data_engine.get_option_price_realtime(prediction['contract_symbol'])
        
        if not current_data:
            logger.warning(f"⚠️ Cannot get current price for {prediction['contract_symbol']}")
            return None
        
        current_price = current_data['mid_price']
        entry_price = position['execution']['execution_price']
        
        # Calculate current P&L percentage
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Check profit target
        if pnl_pct >= options_config.PROFIT_TARGET_PCT:
            return 'PROFIT_TARGET'
        
        # Check stop loss
        if pnl_pct <= -options_config.STOP_LOSS_PCT:
            return 'STOP_LOSS'
        
        # Check time decay (close before expiration)
        exp_date = datetime.strptime(prediction['expiry'], "%Y-%m-%d")
        days_to_expiry = (exp_date - datetime.now()).days
        
        if days_to_expiry <= 1:
            return 'TIME_DECAY'
        
        # Check if held too long (25% of original DTE)
        original_dte = prediction['days_to_expiry']
        max_hold_days = max(1, original_dte // 4)
        days_held = (datetime.now() - entry_timestamp).days
        
        if days_held >= max_hold_days:
            return 'MAX_HOLD_TIME'
        
        return None
    
    def close_position(self, prediction_id: str, exit_reason: str) -> bool:
        """Close an open position"""
        
        if prediction_id not in self.open_positions:
            logger.error(f"❌ Position {prediction_id} not found")
            return False
        
        position = self.open_positions[prediction_id]
        prediction = position['prediction']
        
        # Simulate exit execution
        exit_prediction = prediction.copy()
        exit_execution = self._simulate_execution(exit_prediction, 'CLOSE')
        
        if not exit_execution:
            logger.error(f"❌ Failed to close position {prediction_id}")
            return False
        
        # Calculate P&L
        entry_cost = position['execution']['total_cost']
        exit_proceeds = exit_execution['gross_cost']  # What we receive
        exit_commission = exit_execution['commission']
        
        gross_pnl = exit_proceeds - (entry_cost - position['execution']['commission'])  # Exclude entry commission from cost basis
        net_pnl = gross_pnl - exit_commission
        pnl_percentage = net_pnl / (entry_cost - position['execution']['commission'])
        
        # Update account balance
        old_balance = self.account_balance
        self.account_balance += exit_proceeds - exit_commission
        self.total_pnl += net_pnl
        
        # Calculate performance metrics
        entry_timestamp = position['entry_timestamp']
        days_held = (datetime.now() - entry_timestamp).days
        
        # Get stock performance for comparison
        stock_price_entry = prediction.get('stock_price_entry', 0)
        current_stock_price = options_data_engine.get_current_stock_price() or 0
        stock_move_pct = ((current_stock_price - stock_price_entry) / stock_price_entry) if stock_price_entry > 0 else 0
        
        # Create outcome record
        outcome = {
            'prediction_id': prediction_id,
            'exit_timestamp': datetime.now(),
            'exit_price': exit_execution['execution_price'],
            'exit_reason': exit_reason,
            'days_held': days_held,
            'entry_cost': entry_cost,
            'exit_proceeds': exit_proceeds,
            'gross_pnl': gross_pnl,
            'commissions_total': position['execution']['commission'] + exit_commission,
            'net_pnl': net_pnl,
            'pnl_percentage': pnl_percentage,
            'stock_price_exit': current_stock_price,
            'stock_move_pct': stock_move_pct,
            'prediction_accuracy': 1.0 if net_pnl > 0 else 0.0
        }
        
        # Store outcome
        self._store_outcome(outcome)
        
        # Record transaction
        self._record_account_transaction(
            'CLOSE_POSITION', prediction_id, exit_proceeds - exit_commission,
            old_balance, self.account_balance,
            f"Closed {prediction['contract_symbol']} - {exit_reason} (P&L: ${net_pnl:.2f})"
        )
        
        # Move to closed positions
        position['outcome'] = outcome
        position['status'] = 'CLOSED'
        self.closed_positions.append(position)
        del self.open_positions[prediction_id]
        
        pnl_emoji = "💰" if net_pnl > 0 else "💸"
        logger.success(
            f"{pnl_emoji} Closed {prediction['contract_symbol']}: {exit_reason} "
            f"P&L: ${net_pnl:.2f} ({pnl_percentage:.1%}) in {days_held} days"
        )
        
        return True
    
    def _store_prediction(self, prediction: Dict, execution: Dict):
        """Store prediction in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current stock price
        stock_price = options_data_engine.get_current_stock_price() or 0
        
        cursor.execute("""
        INSERT INTO options_predictions (
            prediction_id, symbol, action, contract_symbol, option_type, strike, expiry, days_to_expiry,
            entry_price, contracts, total_cost, commission,
            direction, confidence, expected_move, expected_profit_pct,
            implied_volatility, delta_entry, gamma_entry, theta_entry, vega_entry,
            profit_target_price, stop_loss_price, max_loss_dollars,
            stock_price_entry, volume, open_interest,
            signals_data, reasoning, account_balance_at_entry
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction['prediction_id'], prediction['symbol'], prediction['action'],
            prediction['contract_symbol'], prediction['option_type'], prediction['strike'],
            prediction['expiry'], prediction['days_to_expiry'],
            execution['execution_price'], prediction['contracts'], execution['total_cost'], execution['commission'],
            prediction['direction'], prediction['confidence'], prediction['expected_move'], prediction['expected_profit_pct'],
            prediction['implied_volatility'], prediction.get('delta', 0), prediction.get('gamma', 0),
            prediction.get('theta', 0), prediction.get('vega', 0),
            prediction['profit_target_price'], prediction['stop_loss_price'], prediction['max_loss_dollars'],
            stock_price, prediction['volume'], prediction['open_interest'],
            json.dumps(prediction.get('individual_signals', {})), prediction['reasoning'], self.account_balance
        ))
        
        conn.commit()
        conn.close()
    
    def _store_outcome(self, outcome: Dict):
        """Store trade outcome in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO options_outcomes (
            prediction_id, exit_timestamp, exit_price, exit_reason, days_held,
            entry_cost, exit_proceeds, gross_pnl, commissions_total, net_pnl, pnl_percentage,
            stock_price_exit, stock_move_pct, prediction_accuracy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            outcome['prediction_id'], outcome['exit_timestamp'], outcome['exit_price'], outcome['exit_reason'], outcome['days_held'],
            outcome['entry_cost'], outcome['exit_proceeds'], outcome['gross_pnl'], outcome['commissions_total'],
            outcome['net_pnl'], outcome['pnl_percentage'], outcome['stock_price_exit'], outcome['stock_move_pct'], outcome['prediction_accuracy']
        ))
        
        conn.commit()
        conn.close()
    
    def _record_account_transaction(self, action: str, trade_id: str, amount: float, balance_before: float, balance_after: float, description: str):
        """Record account transaction"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO account_history (action, trade_id, amount, balance_before, balance_after, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (action, trade_id, amount, balance_before, balance_after, description))
        
        conn.commit()
        conn.close()
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get overall stats
        cursor.execute("""
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
            AVG(net_pnl) as avg_pnl,
            SUM(net_pnl) as total_pnl,
            AVG(pnl_percentage) as avg_return_pct,
            AVG(days_held) as avg_days_held,
            MAX(net_pnl) as best_trade,
            MIN(net_pnl) as worst_trade
        FROM options_outcomes
        """)
        
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            total_trades, winning_trades, avg_pnl, total_pnl, avg_return_pct, avg_days_held, best_trade, worst_trade = result
            win_rate = winning_trades / total_trades
            
            # Calculate profit factor
            cursor.execute("SELECT SUM(net_pnl) FROM options_outcomes WHERE net_pnl > 0")
            total_wins = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT ABS(SUM(net_pnl)) FROM options_outcomes WHERE net_pnl < 0")
            total_losses = cursor.fetchone()[0] or 1
            
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
        else:
            total_trades = winning_trades = 0
            win_rate = avg_pnl = total_pnl = avg_return_pct = avg_days_held = 0
            best_trade = worst_trade = profit_factor = 0
        
        conn.close()
        
        return {
            'account_balance': self.account_balance,
            'starting_balance': 1000.0,
            'total_return': self.account_balance - 1000.0,
            'total_return_pct': (self.account_balance - 1000.0) / 1000.0,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_pnl_per_trade': avg_pnl or 0,
            'avg_return_pct': avg_return_pct or 0,
            'avg_days_held': avg_days_held or 0,
            'best_trade': best_trade or 0,
            'worst_trade': worst_trade or 0,
            'open_positions_count': len(self.open_positions),
            'closed_positions_count': len(self.closed_positions)
        }
    
    def get_open_positions_summary(self) -> List[Dict]:
        """Get summary of all open positions"""
        
        summaries = []
        
        for prediction_id, position in self.open_positions.items():
            prediction = position['prediction']
            entry_timestamp = position['entry_timestamp']
            
            # Get current P&L
            current_data = options_data_engine.get_option_price_realtime(prediction['contract_symbol'])
            
            if current_data:
                current_price = current_data['mid_price']
                entry_price = position['execution']['execution_price']
                unrealized_pnl = (current_price - entry_price) * 100 * prediction['contracts']
                unrealized_pnl_pct = (current_price - entry_price) / entry_price
            else:
                unrealized_pnl = unrealized_pnl_pct = 0
            
            days_held = (datetime.now() - entry_timestamp).days
            
            summaries.append({
                'prediction_id': prediction_id,
                'contract_symbol': prediction['contract_symbol'],
                'action': prediction['action'],
                'contracts': prediction['contracts'],
                'entry_price': position['execution']['execution_price'],
                'current_price': current_data['mid_price'] if current_data else 0,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'days_held': days_held,
                'confidence': prediction['confidence']
            })
        
        return summaries

# Create global instance
options_paper_trader = OptionsPaperTrader()

if __name__ == "__main__":
    # Test the paper trader
    logger.info("🧪 Testing Options Paper Trader...")
    
    trader = OptionsPaperTrader()
    
    # Get performance summary
    summary = trader.get_performance_summary()
    print(f"Account Balance: ${summary['account_balance']:.2f}")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']:.1%}")
    print(f"Open Positions: {summary['open_positions_count']}")