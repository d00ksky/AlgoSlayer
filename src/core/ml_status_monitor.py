#!/usr/bin/env python3
"""
ML Status Monitor - Comprehensive Machine Learning Health Tracking
Provides automated Telegram notifications about ML learning progress
"""

import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
from pathlib import Path

class MLStatusMonitor:
    """Monitor and report ML learning effectiveness with Telegram notifications"""
    
    def __init__(self):
        self.db_path = "data/algoslayer_multi_strategy.db"
        self.learning_data_path = "simulation_learning_data.json"
        self.last_notification_path = "data/last_ml_notification.json"
        self.notification_interval_hours = 3  # Notify every 3 hours during market
        
    def get_comprehensive_ml_status(self) -> Dict:
        """Get complete ML system status for detailed reporting"""
        
        try:
            # Load learning data
            learning_data = self._load_learning_data()
            
            # Get current performance metrics
            performance_metrics = self._get_performance_metrics()
            
            # Get strategy comparison
            strategy_comparison = self._get_strategy_comparison()
            
            # Get learning effectiveness
            learning_effectiveness = self._analyze_learning_effectiveness()
            
            # Get prediction volume and quality
            prediction_quality = self._get_prediction_quality_metrics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "learning_data": learning_data,
                "performance_metrics": performance_metrics,
                "strategy_comparison": strategy_comparison,
                "learning_effectiveness": learning_effectiveness,
                "prediction_quality": prediction_quality,
                "overall_health": self._calculate_overall_health(
                    performance_metrics, learning_effectiveness, prediction_quality
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting ML status: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _load_learning_data(self) -> Dict:
        """Load simulation learning data"""
        try:
            if Path(self.learning_data_path).exists():
                with open(self.learning_data_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def _get_performance_metrics(self) -> Dict:
        """Get recent performance metrics across all strategies"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get last 24 hours performance
                query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    COUNT(CASE WHEN o.net_pnl > 0 THEN 1 END) as winning_predictions,
                    AVG(CASE WHEN o.net_pnl > 0 THEN 1.0 ELSE 0.0 END) * 100 as win_rate,
                    AVG(p.confidence) * 100 as avg_confidence,
                    SUM(o.net_pnl) as total_pnl,
                    COUNT(DISTINCT p.strategy_id) as active_strategies
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.timestamp >= datetime('now', '-24 hours')
                """
                
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result:
                    return {
                        "total_predictions": result[0] or 0,
                        "winning_predictions": result[1] or 0,
                        "win_rate": result[2] or 0,
                        "avg_confidence": result[3] or 0,
                        "total_pnl": result[4] or 0,
                        "active_strategies": result[5] or 0
                    }
                
        except Exception as e:
            logger.error(f"❌ Error getting performance metrics: {e}")
            
        return {"error": "No data available"}
    
    def _get_strategy_comparison(self) -> Dict:
        """Compare strategy performance over last 7 days"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    p.strategy_id,
                    COUNT(*) as predictions,
                    COUNT(CASE WHEN o.net_pnl > 0 THEN 1 END) as wins,
                    AVG(CASE WHEN o.net_pnl > 0 THEN 1.0 ELSE 0.0 END) * 100 as win_rate,
                    AVG(p.confidence) * 100 as avg_confidence,
                    SUM(o.net_pnl) as total_pnl,
                    AVG(o.net_pnl) as avg_pnl
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.timestamp >= datetime('now', '-7 days')
                GROUP BY p.strategy_id
                ORDER BY total_pnl DESC
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                strategies = {}
                for row in results:
                    strategies[row[0]] = {
                        "predictions": row[1],
                        "wins": row[2] or 0,
                        "win_rate": row[3] or 0,
                        "avg_confidence": row[4] or 0,
                        "total_pnl": row[5] or 0,
                        "avg_pnl": row[6] or 0
                    }
                
                return strategies
                
        except Exception as e:
            logger.error(f"❌ Error getting strategy comparison: {e}")
            return {}
    
    def _analyze_learning_effectiveness(self) -> Dict:
        """Analyze how effective the ML learning has been"""
        
        learning_data = self._load_learning_data()
        if not learning_data:
            return {"status": "no_learning_data"}
        
        try:
            # Compare current thresholds with original
            applied_thresholds = learning_data.get('applied_thresholds', {})
            original_simulation = learning_data.get('simulation_results', {})
            
            effectiveness = {
                "learning_applied": len(applied_thresholds) > 0,
                "strategies_enhanced": len(applied_thresholds),
                "avg_threshold_boost": 0,
                "expected_improvements": {},
                "learning_timestamp": learning_data.get('timestamp', 'Unknown')
            }
            
            if applied_thresholds:
                # Calculate average threshold improvement
                boosts = []
                for strategy, data in applied_thresholds.items():
                    if 'boost_percentage' in data:
                        boosts.append(data['boost_percentage'])
                
                if boosts:
                    effectiveness["avg_threshold_boost"] = sum(boosts) / len(boosts)
            
            return effectiveness
            
        except Exception as e:
            logger.error(f"❌ Error analyzing learning effectiveness: {e}")
            return {"error": str(e)}
    
    def _get_prediction_quality_metrics(self) -> Dict:
        """Analyze prediction quality and volume trends"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get prediction quality over last 3 days
                query = """
                SELECT 
                    DATE(p.timestamp) as date,
                    COUNT(*) as predictions,
                    AVG(p.confidence) * 100 as avg_confidence,
                    COUNT(CASE WHEN p.confidence >= 0.70 THEN 1 END) as high_confidence,
                    COUNT(CASE WHEN p.confidence >= 0.80 THEN 1 END) as very_high_confidence
                FROM predictions p
                WHERE p.timestamp >= datetime('now', '-3 days')
                GROUP BY DATE(p.timestamp)
                ORDER BY date DESC
                """
                
                cursor.execute(query)
                daily_quality = cursor.fetchall()
                
                quality_trend = []
                for row in daily_quality:
                    quality_trend.append({
                        "date": row[0],
                        "predictions": row[1],
                        "avg_confidence": row[2] or 0,
                        "high_confidence": row[3],
                        "very_high_confidence": row[4]
                    })
                
                return {
                    "daily_trend": quality_trend,
                    "trend_analysis": self._analyze_quality_trend(quality_trend)
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting prediction quality: {e}")
            return {"error": str(e)}
    
    def _analyze_quality_trend(self, daily_data: List[Dict]) -> Dict:
        """Analyze if prediction quality is improving"""
        
        if len(daily_data) < 2:
            return {"status": "insufficient_data"}
        
        # Compare latest day vs previous
        latest = daily_data[0]
        previous = daily_data[1]
        
        confidence_change = latest["avg_confidence"] - previous["avg_confidence"]
        volume_change = latest["predictions"] - previous["predictions"]
        
        return {
            "confidence_trend": "improving" if confidence_change > 0 else "declining" if confidence_change < 0 else "stable",
            "confidence_change": confidence_change,
            "volume_trend": "increasing" if volume_change > 0 else "decreasing" if volume_change < 0 else "stable",
            "volume_change": volume_change,
            "quality_score": self._calculate_quality_score(latest)
        }
    
    def _calculate_quality_score(self, data: Dict) -> float:
        """Calculate overall quality score (0-100)"""
        
        # Weight different factors
        confidence_score = min(data["avg_confidence"], 100) * 0.4
        high_conf_ratio = (data["high_confidence"] / max(data["predictions"], 1)) * 100 * 0.3
        very_high_conf_ratio = (data["very_high_confidence"] / max(data["predictions"], 1)) * 100 * 0.2
        volume_score = min(data["predictions"] * 5, 100) * 0.1  # Up to 20 predictions = 100 points
        
        return confidence_score + high_conf_ratio + very_high_conf_ratio + volume_score
    
    def _calculate_overall_health(self, performance: Dict, learning: Dict, quality: Dict) -> Dict:
        """Calculate overall ML system health score"""
        
        health_score = 0
        health_factors = []
        
        # Performance health (40% weight)
        if "win_rate" in performance and performance["win_rate"] > 0:
            perf_score = min(performance["win_rate"], 100) * 0.4
            health_score += perf_score
            health_factors.append(f"Win Rate: {performance['win_rate']:.1f}%")
        
        # Learning application health (30% weight)
        if learning.get("learning_applied", False):
            learning_score = 30
            health_score += learning_score
            health_factors.append(f"Learning: Active ({learning.get('strategies_enhanced', 0)} strategies)")
        
        # Prediction quality health (30% weight)
        if "trend_analysis" in quality and "quality_score" in quality["trend_analysis"]:
            qual_score = min(quality["trend_analysis"]["quality_score"], 100) * 0.3
            health_score += qual_score
            health_factors.append(f"Quality: {quality['trend_analysis']['quality_score']:.1f}/100")
        
        # Determine health status
        if health_score >= 80:
            status = "EXCELLENT"
            emoji = "🟢"
        elif health_score >= 60:
            status = "GOOD"  
            emoji = "🟡"
        elif health_score >= 40:
            status = "FAIR"
            emoji = "🟠"
        else:
            status = "NEEDS_ATTENTION"
            emoji = "🔴"
        
        return {
            "score": health_score,
            "status": status,
            "emoji": emoji,
            "factors": health_factors
        }
    
    def should_send_notification(self) -> bool:
        """Check if enough time has passed to send another notification"""
        
        try:
            if not Path(self.last_notification_path).exists():
                return True
            
            with open(self.last_notification_path, 'r') as f:
                last_data = json.load(f)
            
            last_time = datetime.fromisoformat(last_data["timestamp"])
            time_since = datetime.now() - last_time
            
            # Send notification if:
            # 1. More than interval hours have passed
            # 2. It's during market hours (9:30 AM - 4 PM ET)
            # 3. It's a weekday
            
            now = datetime.now()
            is_weekday = now.weekday() < 5
            is_market_hours = 9.5 <= now.hour <= 16
            
            return (time_since.total_seconds() >= self.notification_interval_hours * 3600 
                    and is_market_hours and is_weekday)
            
        except Exception:
            return True
    
    def mark_notification_sent(self):
        """Mark that a notification was sent"""
        
        try:
            Path("data").mkdir(exist_ok=True)
            with open(self.last_notification_path, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "notification_type": "ml_status"
                }, f)
        except Exception as e:
            logger.error(f"❌ Error marking notification sent: {e}")
    
    def format_ml_status_message(self, status_data: Dict) -> str:
        """Format ML status data into a comprehensive Telegram message"""
        
        if "error" in status_data:
            return f"❌ **ML Status Error:** {status_data['error']}"
        
        performance = status_data.get("performance_metrics", {})
        learning = status_data.get("learning_effectiveness", {})
        quality = status_data.get("prediction_quality", {})
        health = status_data.get("overall_health", {})
        strategies = status_data.get("strategy_comparison", {})
        
        # Header
        message = f"""
🧠 **ML SYSTEM STATUS REPORT**
⏰ {datetime.now().strftime('%H:%M:%S ET')}

{health.get('emoji', '⚪')} **Overall Health: {health.get('status', 'UNKNOWN')}** ({health.get('score', 0):.1f}/100)
"""
        
        # Performance Summary
        if "total_predictions" in performance:
            message += f"""
📊 **24H PERFORMANCE:**
   • Predictions: {performance['total_predictions']}
   • Win Rate: {performance['win_rate']:.1f}%
   • Avg Confidence: {performance['avg_confidence']:.1f}%
   • Active Strategies: {performance['active_strategies']}/8
   • P&L: ${performance['total_pnl']:.2f}
"""
        
        # Learning Status
        if learning.get("learning_applied", False):
            message += f"""
🎓 **LEARNING STATUS:**
   • Status: ✅ ACTIVE
   • Enhanced Strategies: {learning['strategies_enhanced']}/8
   • Avg Threshold Boost: +{learning['avg_threshold_boost']:.1f}%
   • Applied: {learning.get('learning_timestamp', 'Unknown')[:10]}
"""
        else:
            message += f"""
🎓 **LEARNING STATUS:**
   • Status: ⚠️ NO LEARNING DATA
   • Recommendation: Run ML training
"""
        
        # Strategy Performance (Top 3)
        if strategies:
            sorted_strategies = sorted(strategies.items(), 
                                     key=lambda x: x[1]['total_pnl'], reverse=True)[:3]
            message += f"""
🏆 **TOP PERFORMERS (7D):**
"""
            for i, (strategy, data) in enumerate(sorted_strategies, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                message += f"   {emoji} {strategy}: {data['win_rate']:.1f}% WR, ${data['total_pnl']:.2f}\n"
        
        # Prediction Quality Trend
        if "trend_analysis" in quality:
            trend = quality["trend_analysis"]
            trend_emoji = "📈" if trend.get("confidence_trend") == "improving" else "📉" if trend.get("confidence_trend") == "declining" else "➖"
            
            message += f"""
📈 **QUALITY TREND:**
   • Confidence: {trend_emoji} {trend.get('confidence_trend', 'unknown').title()}
   • Quality Score: {trend.get('quality_score', 0):.1f}/100
   • Volume: {trend.get('volume_trend', 'unknown').title()}
"""
        
        # Health Factors
        if health.get("factors"):
            message += f"""
🔍 **HEALTH FACTORS:**
"""
            for factor in health["factors"]:
                message += f"   • {factor}\n"
        
        return message.strip()
    
    def format_quick_ml_summary(self, status_data: Dict) -> str:
        """Format a quick ML summary for frequent updates"""
        
        if "error" in status_data:
            return f"❌ ML Error: {status_data['error']}"
        
        performance = status_data.get("performance_metrics", {})
        health = status_data.get("overall_health", {})
        learning = status_data.get("learning_effectiveness", {})
        
        predictions = performance.get("total_predictions", 0)
        win_rate = performance.get("win_rate", 0)
        active_strategies = performance.get("active_strategies", 0)
        
        learning_status = "✅ Active" if learning.get("learning_applied", False) else "⚠️ Inactive"
        
        return f"""
🧠 **Quick ML Status**
{health.get('emoji', '⚪')} Health: {health.get('status', 'Unknown')} | Learning: {learning_status}
📊 24H: {predictions} predictions, {win_rate:.1f}% WR, {active_strategies}/8 strategies active
        """.strip()


# Global instance
ml_status_monitor = MLStatusMonitor()


if __name__ == "__main__":
    # Test the ML status monitor
    monitor = MLStatusMonitor()
    status = monitor.get_comprehensive_ml_status()
    message = monitor.format_ml_status_message(status)
    print(message)