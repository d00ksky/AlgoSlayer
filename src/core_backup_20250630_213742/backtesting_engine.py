"""
Advanced Backtesting Engine
Validates strategy optimizations against historical RTX options data
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
import json

class BacktestingEngine:
    """Comprehensive backtesting system for strategy validation"""
    
    def __init__(self):
        self.db_path = "/opt/rtx-trading/data/algoslayer_main.db"
        self.backtest_results = {}
        
        # Backtesting parameters
        self.initial_balance = 1000
        self.commission_per_contract = 0.65
        self.commission_per_trade = 0.50
        
        # Strategy configurations for backtesting
        self.strategy_configs = {
            "current_system": {
                "confidence_threshold": 0.75,
                "signal_agreement": 4,
                "position_size_pct": 0.20,
                "use_kelly": True,
                "use_iv_optimization": True,
                "use_earnings_timing": True
            },
            "pre_optimization": {
                "confidence_threshold": 0.60,
                "signal_agreement": 3,
                "position_size_pct": 0.20,
                "use_kelly": False,
                "use_iv_optimization": False,
                "use_earnings_timing": False
            },
            "aggressive_test": {
                "confidence_threshold": 0.65,
                "signal_agreement": 3,
                "position_size_pct": 0.25,
                "use_kelly": True,
                "use_iv_optimization": True,
                "use_earnings_timing": True
            }
        }
    
    def run_historical_backtest(self, 
                               strategy_name: str, 
                               start_date: str, 
                               end_date: str) -> Dict:
        """Run backtest on historical data for specified strategy"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get historical predictions and outcomes
                query = """
                SELECT 
                    p.prediction_id,
                    p.timestamp,
                    p.confidence,
                    p.expected_move,
                    p.direction,
                    o.net_pnl,
                    o.pnl_percentage,
                    o.exit_reason,
                    COUNT(st.signal_name) as signal_count
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                LEFT JOIN signal_tracking st ON p.prediction_id = st.prediction_id
                WHERE p.timestamp BETWEEN ? AND ?
                GROUP BY p.prediction_id
                ORDER BY p.timestamp
                """
                
                cursor.execute(query, (start_date, end_date))
                historical_data = cursor.fetchall()
                
                if not historical_data:
                    return {"status": "no_data", "period": f"{start_date} to {end_date}"}
                
                # Run backtest simulation
                results = self._simulate_strategy(historical_data, strategy_name)
                
                return {
                    "status": "success",
                    "strategy": strategy_name,
                    "period": f"{start_date} to {end_date}",
                    "total_trades": len(historical_data),
                    "results": results
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _simulate_strategy(self, historical_data: List, strategy_name: str) -> Dict:
        """Simulate strategy performance on historical data"""
        
        config = self.strategy_configs.get(strategy_name, self.strategy_configs["current_system"])
        
        balance = self.initial_balance
        total_trades = 0
        winning_trades = 0
        total_pnl = 0
        max_drawdown = 0
        peak_balance = self.initial_balance
        
        trade_log = []
        
        for trade_data in historical_data:
            (prediction_id, timestamp, confidence, expected_move, 
             direction, net_pnl, pnl_percentage, exit_reason, signal_count) = trade_data
            
            # Apply strategy filters
            if not self._should_take_trade(confidence, signal_count, config):
                continue
            
            # Calculate position size based on strategy
            position_size = self._calculate_position_size(balance, confidence, config)
            
            # Apply historical outcome (if available)
            if net_pnl is not None:
                # Simulate the trade
                trade_pnl = net_pnl * (position_size / 200)  # Scale based on position size
                
                # Apply commissions
                commission = self.commission_per_contract + self.commission_per_trade
                trade_pnl -= commission
                
                balance += trade_pnl
                total_pnl += trade_pnl
                total_trades += 1
                
                if trade_pnl > 0:
                    winning_trades += 1
                
                # Track drawdown
                if balance > peak_balance:
                    peak_balance = balance
                current_drawdown = (peak_balance - balance) / peak_balance
                max_drawdown = max(max_drawdown, current_drawdown)
                
                # Log trade
                trade_log.append({
                    "timestamp": timestamp,
                    "confidence": confidence,
                    "direction": direction,
                    "position_size": position_size,
                    "pnl": trade_pnl,
                    "balance": balance
                })
        
        # Calculate performance metrics
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_return = (balance - self.initial_balance) / self.initial_balance
        
        return {
            "final_balance": round(balance, 2),
            "total_return": round(total_return, 4),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": round(win_rate, 4),
            "total_pnl": round(total_pnl, 2),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": self._calculate_sharpe_ratio(trade_log),
            "trade_log": trade_log[-10:] if len(trade_log) > 10 else trade_log  # Last 10 trades
        }
    
    def _should_take_trade(self, confidence: float, signal_count: int, config: Dict) -> bool:
        """Determine if trade meets strategy criteria"""
        
        if confidence < config["confidence_threshold"]:
            return False
        
        if signal_count < config["signal_agreement"]:
            return False
        
        return True
    
    def _calculate_position_size(self, balance: float, confidence: float, config: Dict) -> float:
        """Calculate position size based on strategy configuration"""
        
        if config.get("use_kelly", False):
            # Simplified Kelly calculation for backtesting
            kelly_fraction = min(confidence * 0.3, 0.25)  # Max 25%
            return balance * kelly_fraction
        else:
            # Fixed percentage
            return balance * config["position_size_pct"]
    
    def _calculate_sharpe_ratio(self, trade_log: List) -> float:
        """Calculate Sharpe ratio from trade log"""
        
        if len(trade_log) < 5:
            return 0.0
        
        returns = []
        for i in range(1, len(trade_log)):
            prev_balance = trade_log[i-1]["balance"]
            curr_balance = trade_log[i]["balance"]
            daily_return = (curr_balance - prev_balance) / prev_balance
            returns.append(daily_return)
        
        if not returns:
            return 0.0
        
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        
        return round(avg_return / std_return if std_return > 0 else 0.0, 2)
    
    def compare_strategies(self, strategies: List[str], start_date: str, end_date: str) -> Dict:
        """Compare multiple strategies side by side"""
        
        comparison_results = {}
        
        for strategy in strategies:
            results = self.run_historical_backtest(strategy, start_date, end_date)
            if results["status"] == "success":
                comparison_results[strategy] = results["results"]
        
        # Generate comparison summary
        if len(comparison_results) > 1:
            best_strategy = max(comparison_results.keys(), 
                              key=lambda k: comparison_results[k]["total_return"])
            
            return {
                "status": "success",
                "comparison": comparison_results,
                "best_strategy": best_strategy,
                "improvement": self._calculate_improvement(comparison_results)
            }
        
        return {"status": "insufficient_data"}
    
    def _calculate_improvement(self, results: Dict) -> Dict:
        """Calculate improvement between strategies"""
        
        if "current_system" in results and "pre_optimization" in results:
            current = results["current_system"]
            previous = results["pre_optimization"]
            
            return {
                "return_improvement": current["total_return"] - previous["total_return"],
                "win_rate_improvement": current["win_rate"] - previous["win_rate"],
                "drawdown_improvement": previous["max_drawdown"] - current["max_drawdown"],
                "trades_improvement": current["total_trades"] - previous["total_trades"]
            }
        
        return {}
    
    def generate_backtest_report(self, strategy: str, start_date: str, end_date: str) -> str:
        """Generate comprehensive backtesting report"""
        
        results = self.run_historical_backtest(strategy, start_date, end_date)
        
        if results["status"] != "success":
            return f"❌ **BACKTESTING FAILED**: {results.get('message', 'Unknown error')}"
        
        data = results["results"]
        
        report = f"""
🔬 **BACKTESTING REPORT**

📊 **Strategy**: {strategy.upper()}
📅 **Period**: {results['period']}
🎯 **Total Trades**: {data['total_trades']}

💰 **Performance**:
• Final Balance: ${data['final_balance']:.2f}
• Total Return: {data['total_return']:.1%}
• Win Rate: {data['win_rate']:.1%} ({data['winning_trades']}/{data['total_trades']})
• Total P&L: ${data['total_pnl']:.2f}

📉 **Risk Metrics**:
• Max Drawdown: {data['max_drawdown']:.1%}
• Sharpe Ratio: {data['sharpe_ratio']}

🎯 **Recommendation**: {"✅ VALIDATED" if data['total_return'] > 0.1 else "⚠️ NEEDS IMPROVEMENT"}
"""
        return report.strip()

# Global instance
backtesting_engine = BacktestingEngine()
