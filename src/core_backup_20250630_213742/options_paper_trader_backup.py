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
    
    def _simulate_execution(self, prediction: Dict, action: str) -> Optional[Dict]:\n        """Simulate realistic order execution with slippage and timing"""\n        \n        try:\n            # Get current option price\n            current_data = options_data_engine.get_option_price_realtime(prediction['contract_symbol'])\n            \n            if not current_data:\n                logger.error(f"❌ Cannot get current price for {prediction['contract_symbol']}")\n                return None\n            \n            if action == 'OPEN':\n                # We pay the ask price (market order)\n                execution_price = current_data['ask']\n                \n                # Add slippage for larger orders\n                contracts = prediction['contracts']\n                if contracts > 5:\n                    slippage = 0.02 * execution_price  # 2% slippage\n                    execution_price += slippage\n                    logger.info(f"📊 Applied slippage: +${slippage:.2f}")\n                \n            else:  # CLOSE\n                # We get the bid price (market order)\n                execution_price = current_data['bid']\n                \n                # Subtract slippage for larger orders\n                contracts = prediction['contracts']\n                if contracts > 5:\n                    slippage = 0.02 * execution_price  # 2% slippage\n                    execution_price -= slippage\n                    logger.info(f"📊 Applied slippage: -${slippage:.2f}")\n            \n            # Calculate costs\n            cost_per_contract = execution_price * 100\n            gross_cost = cost_per_contract * prediction['contracts']\n            commission = options_config.calculate_commission(action, prediction['contracts'])\n            total_cost = gross_cost + commission\n            \n            return {\n                'execution_price': execution_price,\n                'cost_per_contract': cost_per_contract,\n                'gross_cost': gross_cost,\n                'commission': commission,\n                'total_cost': total_cost,\n                'timestamp': datetime.now(),\n                'current_bid': current_data['bid'],\n                'current_ask': current_data['ask'],\n                'slippage_applied': contracts > 5\n            }\n            \n        except Exception as e:\n            logger.error(f"❌ Execution simulation failed: {e}")\n            return None\n    \n    def check_positions(self) -> List[str]:\n        \"\"\"Check all open positions for exit conditions\"\"\"\n        \n        if not self.open_positions:\n            return []\n        \n        actions_taken = []\n        \n        for prediction_id, position in list(self.open_positions.items()):\n            action = self._check_exit_conditions(position)\n            \n            if action:\n                success = self.close_position(prediction_id, action)\n                if success:\n                    actions_taken.append(f"Closed {prediction_id}: {action}")\n        \n        return actions_taken\n    \n    def _check_exit_conditions(self, position: Dict) -> Optional[str]:\n        \"\"\"Check if position should be closed\"\"\"\n        \n        prediction = position['prediction']\n        entry_timestamp = position['entry_timestamp']\n        \n        # Get current option price\n        current_data = options_data_engine.get_option_price_realtime(prediction['contract_symbol'])\n        \n        if not current_data:\n            logger.warning(f"⚠️ Cannot get current price for {prediction['contract_symbol']}")\n            return None\n        \n        current_price = current_data['mid_price']\n        entry_price = position['execution']['execution_price']\n        \n        # Calculate current P&L percentage\n        pnl_pct = (current_price - entry_price) / entry_price\n        \n        # Check profit target\n        if pnl_pct >= options_config.PROFIT_TARGET_PCT:\n            return 'PROFIT_TARGET'\n        \n        # Check stop loss\n        if pnl_pct <= -options_config.STOP_LOSS_PCT:\n            return 'STOP_LOSS'\n        \n        # Check time decay (close before expiration)\n        exp_date = datetime.strptime(prediction['expiry'], \"%Y-%m-%d\")\n        days_to_expiry = (exp_date - datetime.now()).days\n        \n        if days_to_expiry <= 1:\n            return 'TIME_DECAY'\n        \n        # Check if held too long (25% of original DTE)\n        original_dte = prediction['days_to_expiry']\n        max_hold_days = max(1, original_dte // 4)\n        days_held = (datetime.now() - entry_timestamp).days\n        \n        if days_held >= max_hold_days:\n            return 'MAX_HOLD_TIME'\n        \n        return None\n    \n    def close_position(self, prediction_id: str, exit_reason: str) -> bool:\n        \"\"\"Close an open position\"\"\"\n        \n        if prediction_id not in self.open_positions:\n            logger.error(f"❌ Position {prediction_id} not found")\n            return False\n        \n        position = self.open_positions[prediction_id]\n        prediction = position['prediction']\n        \n        # Simulate exit execution\n        exit_prediction = prediction.copy()\n        exit_execution = self._simulate_execution(exit_prediction, 'CLOSE')\n        \n        if not exit_execution:\n            logger.error(f"❌ Failed to close position {prediction_id}")\n            return False\n        \n        # Calculate P&L\n        entry_cost = position['execution']['total_cost']\n        exit_proceeds = exit_execution['gross_cost']  # What we receive\n        exit_commission = exit_execution['commission']\n        \n        gross_pnl = exit_proceeds - (entry_cost - position['execution']['commission'])  # Exclude entry commission from cost basis\n        net_pnl = gross_pnl - exit_commission\n        pnl_percentage = net_pnl / (entry_cost - position['execution']['commission'])\n        \n        # Update account balance\n        old_balance = self.account_balance\n        self.account_balance += exit_proceeds - exit_commission\n        self.total_pnl += net_pnl\n        \n        # Calculate performance metrics\n        entry_timestamp = position['entry_timestamp']\n        days_held = (datetime.now() - entry_timestamp).days\n        \n        # Get stock performance for comparison\n        stock_price_entry = prediction.get('stock_price_entry', 0)\n        current_stock_price = options_data_engine.get_current_stock_price() or 0\n        stock_move_pct = ((current_stock_price - stock_price_entry) / stock_price_entry) if stock_price_entry > 0 else 0\n        \n        # Create outcome record\n        outcome = {\n            'prediction_id': prediction_id,\n            'exit_timestamp': datetime.now(),\n            'exit_price': exit_execution['execution_price'],\n            'exit_reason': exit_reason,\n            'days_held': days_held,\n            'entry_cost': entry_cost,\n            'exit_proceeds': exit_proceeds,\n            'gross_pnl': gross_pnl,\n            'commissions_total': position['execution']['commission'] + exit_commission,\n            'net_pnl': net_pnl,\n            'pnl_percentage': pnl_percentage,\n            'stock_price_exit': current_stock_price,\n            'stock_move_pct': stock_move_pct,\n            'prediction_accuracy': 1.0 if net_pnl > 0 else 0.0\n        }\n        \n        # Store outcome\n        self._store_outcome(outcome)\n        \n        # Record transaction\n        self._record_account_transaction(\n            'CLOSE_POSITION', prediction_id, exit_proceeds - exit_commission,\n            old_balance, self.account_balance,\n            f"Closed {prediction['contract_symbol']} - {exit_reason} (P&L: ${net_pnl:.2f})"\n        )\n        \n        # Move to closed positions\n        position['outcome'] = outcome\n        position['status'] = 'CLOSED'\n        self.closed_positions.append(position)\n        del self.open_positions[prediction_id]\n        \n        pnl_emoji = \"💰\" if net_pnl > 0 else \"💸\"\n        logger.success(\n            f\"{pnl_emoji} Closed {prediction['contract_symbol']}: {exit_reason} \"\n            f\"P&L: ${net_pnl:.2f} ({pnl_percentage:.1%}) in {days_held} days\"\n        )\n        \n        return True\n    \n    def _store_prediction(self, prediction: Dict, execution: Dict):\n        \"\"\"Store prediction in database\"\"\"\n        \n        conn = sqlite3.connect(self.db_path)\n        cursor = conn.cursor()\n        \n        # Get current stock price\n        stock_price = options_data_engine.get_current_stock_price() or 0\n        \n        cursor.execute(\"\"\"\n        INSERT INTO options_predictions (\n            prediction_id, symbol, action, contract_symbol, option_type, strike, expiry, days_to_expiry,\n            entry_price, contracts, total_cost, commission,\n            direction, confidence, expected_move, expected_profit_pct,\n            implied_volatility, delta_entry, gamma_entry, theta_entry, vega_entry,\n            profit_target_price, stop_loss_price, max_loss_dollars,\n            stock_price_entry, volume, open_interest,\n            signals_data, reasoning, account_balance_at_entry\n        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n        \"\"\", (\n            prediction['prediction_id'], prediction['symbol'], prediction['action'],\n            prediction['contract_symbol'], prediction['option_type'], prediction['strike'],\n            prediction['expiry'], prediction['days_to_expiry'],\n            execution['execution_price'], prediction['contracts'], execution['total_cost'], execution['commission'],\n            prediction['direction'], prediction['confidence'], prediction['expected_move'], prediction['expected_profit_pct'],\n            prediction['implied_volatility'], prediction.get('delta', 0), prediction.get('gamma', 0),\n            prediction.get('theta', 0), prediction.get('vega', 0),\n            prediction['profit_target_price'], prediction['stop_loss_price'], prediction['max_loss_dollars'],\n            stock_price, prediction['volume'], prediction['open_interest'],\n            json.dumps(prediction.get('individual_signals', {})), prediction['reasoning'], self.account_balance\n        ))\n        \n        conn.commit()\n        conn.close()\n    \n    def _store_outcome(self, outcome: Dict):\n        \"\"\"Store trade outcome in database\"\"\"\n        \n        conn = sqlite3.connect(self.db_path)\n        cursor = conn.cursor()\n        \n        cursor.execute(\"\"\"\n        INSERT INTO options_outcomes (\n            prediction_id, exit_timestamp, exit_price, exit_reason, days_held,\n            entry_cost, exit_proceeds, gross_pnl, commissions_total, net_pnl, pnl_percentage,\n            stock_price_exit, stock_move_pct, prediction_accuracy\n        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n        \"\"\", (\n            outcome['prediction_id'], outcome['exit_timestamp'], outcome['exit_price'], outcome['exit_reason'], outcome['days_held'],\n            outcome['entry_cost'], outcome['exit_proceeds'], outcome['gross_pnl'], outcome['commissions_total'],\n            outcome['net_pnl'], outcome['pnl_percentage'], outcome['stock_price_exit'], outcome['stock_move_pct'], outcome['prediction_accuracy']\n        ))\n        \n        conn.commit()\n        conn.close()\n    \n    def _record_account_transaction(self, action: str, trade_id: str, amount: float, balance_before: float, balance_after: float, description: str):\n        \"\"\"Record account transaction\"\"\"\n        \n        conn = sqlite3.connect(self.db_path)\n        cursor = conn.cursor()\n        \n        cursor.execute(\"\"\"\n        INSERT INTO account_history (action, trade_id, amount, balance_before, balance_after, description)\n        VALUES (?, ?, ?, ?, ?, ?)\n        \"\"\", (action, trade_id, amount, balance_before, balance_after, description))\n        \n        conn.commit()\n        conn.close()\n    \n    def get_performance_summary(self) -> Dict:\n        \"\"\"Get comprehensive performance summary\"\"\"\n        \n        conn = sqlite3.connect(self.db_path)\n        cursor = conn.cursor()\n        \n        # Get overall stats\n        cursor.execute(\"\"\"\n        SELECT \n            COUNT(*) as total_trades,\n            SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,\n            AVG(net_pnl) as avg_pnl,\n            SUM(net_pnl) as total_pnl,\n            AVG(pnl_percentage) as avg_return_pct,\n            AVG(days_held) as avg_days_held,\n            MAX(net_pnl) as best_trade,\n            MIN(net_pnl) as worst_trade\n        FROM options_outcomes\n        \"\"\")\n        \n        result = cursor.fetchone()\n        \n        if result and result[0] > 0:\n            total_trades, winning_trades, avg_pnl, total_pnl, avg_return_pct, avg_days_held, best_trade, worst_trade = result\n            win_rate = winning_trades / total_trades\n            \n            # Calculate profit factor\n            cursor.execute(\"SELECT SUM(net_pnl) FROM options_outcomes WHERE net_pnl > 0\")\n            total_wins = cursor.fetchone()[0] or 0\n            \n            cursor.execute(\"SELECT ABS(SUM(net_pnl)) FROM options_outcomes WHERE net_pnl < 0\")\n            total_losses = cursor.fetchone()[0] or 1\n            \n            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')\n            \n        else:\n            total_trades = winning_trades = 0\n            win_rate = avg_pnl = total_pnl = avg_return_pct = avg_days_held = 0\n            best_trade = worst_trade = profit_factor = 0\n        \n        conn.close()\n        \n        return {\n            'account_balance': self.account_balance,\n            'starting_balance': 1000.0,\n            'total_return': self.account_balance - 1000.0,\n            'total_return_pct': (self.account_balance - 1000.0) / 1000.0,\n            'total_trades': total_trades,\n            'winning_trades': winning_trades,\n            'win_rate': win_rate,\n            'profit_factor': profit_factor,\n            'avg_pnl_per_trade': avg_pnl or 0,\n            'avg_return_pct': avg_return_pct or 0,\n            'avg_days_held': avg_days_held or 0,\n            'best_trade': best_trade or 0,\n            'worst_trade': worst_trade or 0,\n            'open_positions_count': len(self.open_positions),\n            'closed_positions_count': len(self.closed_positions)\n        }\n    \n    def get_open_positions_summary(self) -> List[Dict]:\n        \"\"\"Get summary of all open positions\"\"\"\n        \n        summaries = []\n        \n        for prediction_id, position in self.open_positions.items():\n            prediction = position['prediction']\n            entry_timestamp = position['entry_timestamp']\n            \n            # Get current P&L\n            current_data = options_data_engine.get_option_price_realtime(prediction['contract_symbol'])\n            \n            if current_data:\n                current_price = current_data['mid_price']\n                entry_price = position['execution']['execution_price']\n                unrealized_pnl = (current_price - entry_price) * 100 * prediction['contracts']\n                unrealized_pnl_pct = (current_price - entry_price) / entry_price\n            else:\n                unrealized_pnl = unrealized_pnl_pct = 0\n            \n            days_held = (datetime.now() - entry_timestamp).days\n            \n            summaries.append({\n                'prediction_id': prediction_id,\n                'contract_symbol': prediction['contract_symbol'],\n                'action': prediction['action'],\n                'contracts': prediction['contracts'],\n                'entry_price': position['execution']['execution_price'],\n                'current_price': current_data['mid_price'] if current_data else 0,\n                'unrealized_pnl': unrealized_pnl,\n                'unrealized_pnl_pct': unrealized_pnl_pct,\n                'days_held': days_held,\n                'confidence': prediction['confidence']\n            })\n        \n        return summaries\n\n# Create global instance\noptions_paper_trader = OptionsPaperTrader()\n\nif __name__ == \"__main__\":\n    # Test the paper trader\n    logger.info(\"🧪 Testing Options Paper Trader...\")\n    \n    trader = OptionsPaperTrader()\n    \n    # Get performance summary\n    summary = trader.get_performance_summary()\n    print(f\"Account Balance: ${summary['account_balance']:.2f}\")\n    print(f\"Total Trades: {summary['total_trades']}\")\n    print(f\"Win Rate: {summary['win_rate']:.1%}\")\n    print(f\"Open Positions: {summary['open_positions_count']}\")"