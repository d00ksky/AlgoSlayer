#!/usr/bin/env python3
"""
ML Learning Progress Alerts
Detects significant learning improvements and sends special notifications
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
from pathlib import Path

class MLLearningAlerts:
    """Detect and alert on significant ML learning improvements"""
    
    def __init__(self):
        self.db_path = "data/algoslayer_multi_strategy.db"
        self.alert_history_path = "data/ml_learning_alerts.json"
        self.performance_baseline_path = "data/ml_performance_baseline.json"
        
        # Alert thresholds
        self.significant_improvement_threshold = 0.05  # 5% improvement
        self.major_improvement_threshold = 0.10  # 10% improvement
        self.win_rate_improvement_threshold = 0.03  # 3% win rate improvement
        self.strategy_activation_threshold = 1  # Alert if dormant strategy makes prediction
        
    def check_for_learning_improvements(self) -> List[Dict]:
        """Check for significant learning improvements and return alerts"""
        
        alerts = []
        
        try:
            # Check for strategy improvements
            strategy_alerts = self._check_strategy_improvements()
            alerts.extend(strategy_alerts)
            
            # Check for newly activated strategies
            activation_alerts = self._check_strategy_activations()
            alerts.extend(activation_alerts)
            
            # Check for overall system improvements
            system_alerts = self._check_system_improvements()
            alerts.extend(system_alerts)
            
            # Check for learning effectiveness improvements
            learning_alerts = self._check_learning_effectiveness()
            alerts.extend(learning_alerts)
            
            # Save alerts to history
            if alerts:
                self._save_alerts_to_history(alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error checking learning improvements: {e}")
            return []
    
    def _check_strategy_improvements(self) -> List[Dict]:
        """Check for individual strategy performance improvements"""
        
        alerts = []
        
        try:
            # Get current performance (last 7 days)
            current_performance = self._get_strategy_performance(days=7)
            
            # Get baseline performance (previous 7 days)
            baseline_performance = self._get_strategy_performance(days=14, offset_days=7)
            
            for strategy_id in current_performance.keys():
                current = current_performance[strategy_id]
                baseline = baseline_performance.get(strategy_id, {})
                
                if not baseline or current.get('predictions', 0) < 5:
                    continue  # Need enough data
                
                # Check win rate improvement
                current_wr = current.get('win_rate', 0)
                baseline_wr = baseline.get('win_rate', 0)
                wr_improvement = current_wr - baseline_wr
                
                # Check confidence improvement
                current_conf = current.get('avg_confidence', 0)
                baseline_conf = baseline.get('avg_confidence', 0)
                conf_improvement = current_conf - baseline_conf
                
                # Check PnL improvement
                current_pnl = current.get('avg_pnl', 0)
                baseline_pnl = baseline.get('avg_pnl', 0)
                pnl_improvement = current_pnl - baseline_pnl if baseline_pnl != 0 else 0
                
                # Generate alerts for significant improvements
                if wr_improvement >= self.major_improvement_threshold:
                    alerts.append({
                        "type": "MAJOR_WIN_RATE_IMPROVEMENT",
                        "strategy": strategy_id,
                        "improvement": wr_improvement,
                        "current_value": current_wr,
                        "baseline_value": baseline_wr,
                        "message": f"🚀 MAJOR BREAKTHROUGH: {strategy_id} win rate improved by {wr_improvement:.1%}!",
                        "priority": "HIGH",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif wr_improvement >= self.win_rate_improvement_threshold:
                    alerts.append({
                        "type": "WIN_RATE_IMPROVEMENT", 
                        "strategy": strategy_id,
                        "improvement": wr_improvement,
                        "current_value": current_wr,
                        "baseline_value": baseline_wr,
                        "message": f"📈 Learning Success: {strategy_id} win rate up {wr_improvement:.1%}",
                        "priority": "MEDIUM",
                        "timestamp": datetime.now().isoformat()
                    })
                
                if conf_improvement >= self.significant_improvement_threshold:
                    alerts.append({
                        "type": "CONFIDENCE_IMPROVEMENT",
                        "strategy": strategy_id,
                        "improvement": conf_improvement,
                        "current_value": current_conf,
                        "baseline_value": baseline_conf,
                        "message": f"🎯 Confidence Boost: {strategy_id} confidence up {conf_improvement:.1%}",
                        "priority": "MEDIUM",
                        "timestamp": datetime.now().isoformat()
                    })
                
        except Exception as e:
            logger.error(f"❌ Error checking strategy improvements: {e}")
        
        return alerts
    
    def _check_strategy_activations(self) -> List[Dict]:
        """Check for newly activated strategies making predictions"""
        
        alerts = []
        
        try:
            # Check for strategies that made their first prediction recently
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get strategies with first predictions in last 24 hours
                query = """
                SELECT 
                    strategy_id,
                    MIN(timestamp) as first_prediction,
                    COUNT(*) as prediction_count
                FROM predictions
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY strategy_id
                HAVING first_prediction >= datetime('now', '-24 hours')
                """
                
                cursor.execute(query)
                new_strategies = cursor.fetchall()
                
                for strategy_id, first_prediction, count in new_strategies:
                    # Check if this strategy was dormant before
                    query_history = """
                    SELECT COUNT(*) 
                    FROM predictions 
                    WHERE strategy_id = ? AND timestamp < datetime('now', '-24 hours')
                    """
                    cursor.execute(query_history, (strategy_id,))
                    historical_count = cursor.fetchone()[0]
                    
                    if historical_count == 0:  # Truly new/reactivated strategy
                        alerts.append({
                            "type": "STRATEGY_ACTIVATION",
                            "strategy": strategy_id,
                            "first_prediction": first_prediction,
                            "prediction_count": count,
                            "message": f"🎉 Strategy Activated: {strategy_id} made {count} predictions after reactivation!",
                            "priority": "HIGH",
                            "timestamp": datetime.now().isoformat()
                        })
        
        except Exception as e:
            logger.error(f"❌ Error checking strategy activations: {e}")
        
        return alerts
    
    def _check_system_improvements(self) -> List[Dict]:
        """Check for overall system improvements"""
        
        alerts = []
        
        try:
            # Get system-wide performance metrics
            current_system = self._get_system_performance(days=7)
            baseline_system = self._get_system_performance(days=14, offset_days=7)
            
            if not baseline_system or current_system.get('total_predictions', 0) < 10:
                return alerts
            
            # Check overall win rate improvement
            current_wr = current_system.get('win_rate', 0)
            baseline_wr = baseline_system.get('win_rate', 0)
            wr_improvement = current_wr - baseline_wr
            
            # Check active strategies increase
            current_active = current_system.get('active_strategies', 0)
            baseline_active = baseline_system.get('active_strategies', 0)
            active_increase = current_active - baseline_active
            
            # Check prediction volume increase
            current_volume = current_system.get('daily_avg_predictions', 0)
            baseline_volume = baseline_system.get('daily_avg_predictions', 0)
            volume_increase = current_volume - baseline_volume
            
            if wr_improvement >= self.major_improvement_threshold:
                alerts.append({
                    "type": "SYSTEM_WIN_RATE_BREAKTHROUGH",
                    "improvement": wr_improvement,
                    "current_value": current_wr,
                    "baseline_value": baseline_wr,
                    "message": f"🏆 SYSTEM BREAKTHROUGH: Overall win rate improved by {wr_improvement:.1%}!",
                    "priority": "HIGH",
                    "timestamp": datetime.now().isoformat()
                })
            
            if active_increase >= 2:
                alerts.append({
                    "type": "STRATEGY_ACTIVATION_SURGE",
                    "improvement": active_increase,
                    "current_value": current_active,
                    "baseline_value": baseline_active,
                    "message": f"📊 Strategy Surge: {active_increase} more strategies active ({current_active}/8 total)",
                    "priority": "HIGH",
                    "timestamp": datetime.now().isoformat()
                })
            
            if volume_increase >= 5:
                alerts.append({
                    "type": "PREDICTION_VOLUME_INCREASE",
                    "improvement": volume_increase,
                    "current_value": current_volume,
                    "baseline_value": baseline_volume,
                    "message": f"📈 Volume Increase: {volume_increase:.1f} more predictions per day",
                    "priority": "MEDIUM",
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"❌ Error checking system improvements: {e}")
        
        return alerts
    
    def _check_learning_effectiveness(self) -> List[Dict]:
        """Check if learning system is showing effectiveness"""
        
        alerts = []
        
        try:
            # Load learning data
            learning_data_path = "simulation_learning_data.json"
            if not Path(learning_data_path).exists():
                return alerts
            
            with open(learning_data_path, 'r') as f:
                learning_data = json.load(f)
            
            # Check if learning was recently applied
            applied_thresholds = learning_data.get('applied_thresholds', {})
            if not applied_thresholds:
                return alerts
            
            # Check performance since learning application
            learning_timestamp = learning_data.get('timestamp', '')
            if learning_timestamp:
                learning_date = datetime.fromisoformat(learning_timestamp.replace('Z', '+00:00'))
                days_since_learning = (datetime.now() - learning_date).days
                
                if 1 <= days_since_learning <= 7:  # Check 1-7 days after learning
                    # Get performance since learning
                    performance_since = self._get_system_performance_since(learning_date)
                    
                    if performance_since and performance_since.get('total_predictions', 0) >= 5:
                        win_rate = performance_since.get('win_rate', 0)
                        prediction_count = performance_since['total_predictions']
                        
                        if win_rate >= 0.7:  # 70%+ win rate
                            alerts.append({
                                "type": "LEARNING_EFFECTIVENESS_CONFIRMED",
                                "win_rate": win_rate,
                                "predictions": prediction_count,
                                "days_since_learning": days_since_learning,
                                "message": f"🧠 Learning Confirmed: {win_rate:.1%} win rate over {prediction_count} predictions since ML training",
                                "priority": "HIGH",
                                "timestamp": datetime.now().isoformat()
                            })
                            
        except Exception as e:
            logger.error(f"❌ Error checking learning effectiveness: {e}")
        
        return alerts
    
    def _get_strategy_performance(self, days: int, offset_days: int = 0) -> Dict:
        """Get strategy performance for specified time period"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    p.strategy_id,
                    COUNT(*) as predictions,
                    COUNT(CASE WHEN o.net_pnl > 0 THEN 1 END) as wins,
                    AVG(CASE WHEN o.net_pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                    AVG(p.confidence) as avg_confidence,
                    AVG(o.net_pnl) as avg_pnl
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.timestamp >= datetime('now', '-{} days') 
                AND p.timestamp < datetime('now', '-{} days')
                GROUP BY p.strategy_id
                """.format(days + offset_days, offset_days)
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                performance = {}
                for row in results:
                    performance[row[0]] = {
                        "predictions": row[1],
                        "wins": row[2] or 0,
                        "win_rate": row[3] or 0,
                        "avg_confidence": row[4] or 0,
                        "avg_pnl": row[5] or 0
                    }
                
                return performance
                
        except Exception as e:
            logger.error(f"❌ Error getting strategy performance: {e}")
            return {}
    
    def _get_system_performance(self, days: int, offset_days: int = 0) -> Dict:
        """Get system-wide performance for specified time period"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    COUNT(CASE WHEN o.net_pnl > 0 THEN 1 END) as wins,
                    AVG(CASE WHEN o.net_pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                    COUNT(DISTINCT p.strategy_id) as active_strategies,
                    COUNT(*) * 1.0 / {} as daily_avg_predictions
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.timestamp >= datetime('now', '-{} days')
                AND p.timestamp < datetime('now', '-{} days')
                """.format(days, days + offset_days, offset_days)
                
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result:
                    return {
                        "total_predictions": result[0],
                        "wins": result[1] or 0,
                        "win_rate": result[2] or 0,
                        "active_strategies": result[3],
                        "daily_avg_predictions": result[4] or 0
                    }
                
        except Exception as e:
            logger.error(f"❌ Error getting system performance: {e}")
            
        return {}
    
    def _get_system_performance_since(self, since_date: datetime) -> Dict:
        """Get system performance since specific date"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    COUNT(CASE WHEN o.net_pnl > 0 THEN 1 END) as wins,
                    AVG(CASE WHEN o.net_pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.timestamp >= ?
                """
                
                cursor.execute(query, (since_date.isoformat(),))
                result = cursor.fetchone()
                
                if result:
                    return {
                        "total_predictions": result[0],
                        "wins": result[1] or 0,
                        "win_rate": result[2] or 0
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error getting performance since date: {e}")
            
        return {}
    
    def _save_alerts_to_history(self, alerts: List[Dict]):
        """Save alerts to history file"""
        
        try:
            Path("data").mkdir(exist_ok=True)
            
            # Load existing history
            history = []
            if Path(self.alert_history_path).exists():
                with open(self.alert_history_path, 'r') as f:
                    history = json.load(f)
            
            # Add new alerts
            history.extend(alerts)
            
            # Keep only last 100 alerts
            history = history[-100:]
            
            # Save updated history
            with open(self.alert_history_path, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error saving alerts to history: {e}")
    
    def format_learning_progress_alert(self, alerts: List[Dict]) -> str:
        """Format learning progress alerts into Telegram message"""
        
        if not alerts:
            return ""
        
        # Group alerts by priority
        high_priority = [a for a in alerts if a.get("priority") == "HIGH"]
        medium_priority = [a for a in alerts if a.get("priority") == "MEDIUM"]
        
        message = "🧠 **ML LEARNING PROGRESS ALERT**\n\n"
        
        if high_priority:
            message += "🚨 **HIGH PRIORITY IMPROVEMENTS:**\n"
            for alert in high_priority:
                message += f"   • {alert['message']}\n"
            message += "\n"
        
        if medium_priority:
            message += "📈 **Notable Improvements:**\n"
            for alert in medium_priority:
                message += f"   • {alert['message']}\n"
            message += "\n"
        
        message += f"⏰ Alert Time: {datetime.now().strftime('%H:%M:%S ET')}\n"
        message += "📊 Check /ml_status for detailed analysis"
        
        return message.strip()

# Global instance
ml_learning_alerts = MLLearningAlerts()

if __name__ == "__main__":
    # Test the learning alerts system
    alerts = ml_learning_alerts.check_for_learning_improvements()
    if alerts:
        print("🚨 Learning Improvements Detected:")
        for alert in alerts:
            print(f"   • {alert['message']}")
        
        message = ml_learning_alerts.format_learning_progress_alert(alerts)
        print(f"\nFormatted Message:\n{message}")
    else:
        print("ℹ️ No significant learning improvements detected")