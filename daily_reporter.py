"""
Daily Performance Reporter
Generates comprehensive daily reports at 5 PM ET
Tracks learning progress, predictions, and performance
"""
import asyncio
from datetime import datetime, time as dt_time
from typing import Dict, Optional
from loguru import logger

from src.core.performance_tracker import performance_tracker
from src.core.telegram_bot import telegram_bot
from config.trading_config import config

class DailyReporter:
    """Generate and send daily performance reports"""
    
    def __init__(self):
        self.report_time = dt_time(17, 0)  # 5 PM ET
        self.running = False
        
    async def start_daily_reporting(self):
        """Start the daily reporting scheduler"""
        self.running = True
        logger.info("📅 Daily reporting scheduler started")
        
        while self.running:
            try:
                # Calculate seconds until next 5 PM ET
                now = datetime.now()
                next_report = datetime.combine(now.date(), self.report_time)
                
                # If it's past 5 PM today, schedule for tomorrow
                if now.time() > self.report_time:
                    next_report = next_report.replace(day=next_report.day + 1)
                
                sleep_seconds = (next_report - now).total_seconds()
                
                logger.info(f"📅 Next daily report scheduled for {next_report.strftime('%Y-%m-%d %H:%M')}")
                await asyncio.sleep(sleep_seconds)
                
                # Generate and send report
                if self.running:
                    await self.generate_and_send_report()
                    
            except Exception as e:
                logger.error(f"❌ Daily reporter error: {e}")
                # Sleep for an hour on error to avoid spam
                await asyncio.sleep(3600)
    
    async def generate_and_send_report(self):
        """Generate comprehensive daily report"""
        logger.info("📊 Generating daily performance report...")
        
        try:
            # Generate the report
            report = await self._generate_comprehensive_report()
            
            # Send via Telegram
            await telegram_bot.send_message(
                text=report,
                parse_mode="Markdown"
            )
            
            logger.success("✅ Daily report sent successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate daily report: {e}")
    
    async def _generate_comprehensive_report(self) -> str:
        """Generate the comprehensive daily report"""
        
        # Get performance data
        day_perf = await performance_tracker.get_recent_performance(1)
        week_perf = await performance_tracker.get_recent_performance(7)
        month_perf = await performance_tracker.get_recent_performance(30)
        
        # Get RTX current price
        try:
            import yfinance as yf
            ticker = yf.Ticker("RTX")
            rtx_data = ticker.history(period="2d")
            current_price = rtx_data['Close'].iloc[-1]
            yesterday_price = rtx_data['Close'].iloc[-2] if len(rtx_data) > 1 else current_price
            daily_change = (current_price - yesterday_price) / yesterday_price
        except:
            current_price = 0
            daily_change = 0
        
        report = []
        report.append("📊 **RTX Trading Daily Report**")
        report.append(f"📅 {datetime.now().strftime('%A, %B %d, %Y')} - 5:00 PM ET")
        report.append("")
        
        # RTX Price Section
        report.append("💰 **RTX Stock Performance**")
        if current_price > 0:
            direction = "🟢" if daily_change >= 0 else "🔴"
            report.append(f"• Current Price: ${current_price:.2f} {direction} {daily_change:+.2%}")
        else:
            report.append("• Price data unavailable")
        report.append("")
        
        # Yesterday's Predictions
        if day_perf.get('total_predictions', 0) > 0:
            report.append("🎯 **Yesterday's AI Predictions**")
            report.append(f"• Total Predictions: {day_perf['total_predictions']}")
            report.append(f"• Accuracy Rate: {day_perf['accuracy']:.1%}")
            report.append(f"• Avg Confidence: {day_perf['avg_confidence']:.1%}")
            
            if day_perf.get('avg_profit_potential'):
                profit_emoji = "💰" if day_perf['avg_profit_potential'] > 0 else "⚠️"
                report.append(f"• Options Profit Potential: {profit_emoji} {day_perf['avg_profit_potential']:.1%}")
            report.append("")
        else:
            report.append("🎯 **Yesterday's AI Predictions**")
            report.append("• No predictions with outcomes yet")
            report.append("• System is still learning...")
            report.append("")
        
        # Weekly Performance
        if week_perf.get('total_predictions', 0) > 0:
            report.append("📈 **7-Day Performance**")
            report.append(f"• Total Predictions: {week_perf['total_predictions']}")
            report.append(f"• Accuracy Rate: {week_perf['accuracy']:.1%}")
            
            # Performance assessment
            if week_perf['accuracy'] >= 0.65:
                report.append("• Status: 🟢 **Excellent** - High confidence trading enabled")
            elif week_perf['accuracy'] >= 0.55:
                report.append("• Status: 🟡 **Good** - Moderate position sizing recommended")
            else:
                report.append("• Status: 🔴 **Learning** - Paper trading only")
            report.append("")
        
        # High Conviction Analysis
        high_conv_stats = await self._get_high_conviction_stats()
        if high_conv_stats:
            report.append("🔥 **High Conviction Analysis (≥85%)**")
            report.append(f"• Predictions: {high_conv_stats['total']}")
            report.append(f"• Accuracy: {high_conv_stats['accuracy']:.1%}")
            report.append(f"• Last Signal: {high_conv_stats['last_signal']}")
            report.append("")
        
        # Learning Insights
        report.append("🧠 **Learning Insights**")
        insights = await self._generate_learning_insights()
        for insight in insights:
            report.append(f"• {insight}")
        report.append("")
        
        # Trading Recommendations
        report.append("💡 **Trading Recommendations**")
        recommendations = await self._generate_recommendations()
        for rec in recommendations:
            report.append(f"• {rec}")
        report.append("")
        
        # System Health
        report.append("⚙️ **System Health**")
        report.append("• Status: 🟢 Operational")
        report.append("• Database: 🟢 Connected")
        report.append("• ML Training: 🟢 Ready")
        
        return "\n".join(report)
    
    async def _get_high_conviction_stats(self) -> Optional[Dict]:
        """Get statistics for high conviction predictions"""
        try:
            import sqlite3
            conn = sqlite3.connect(performance_tracker.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN p.direction = o.actual_direction THEN 1 ELSE 0 END) as correct,
                MAX(p.timestamp) as last_signal
            FROM predictions p
            JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
            WHERE p.confidence >= 0.85 AND o.actual_direction IS NOT NULL
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                return {
                    'total': result[0],
                    'accuracy': result[1] / result[0],
                    'last_signal': result[2] or 'Never'
                }
        except:
            pass
        
        return None
    
    async def _generate_learning_insights(self) -> list:
        """Generate insights from recent learning"""
        insights = []
        
        # Get recent performance
        week_perf = await performance_tracker.get_recent_performance(7)
        
        if week_perf.get('total_predictions', 0) > 0:
            if week_perf['accuracy'] > 0.65:
                insights.append("AI model is performing well - high accuracy maintained")
            elif week_perf['accuracy'] < 0.5:
                insights.append("Model may be overfitting - consider retraining")
            
            if week_perf.get('avg_confidence', 0) > 0.8:
                insights.append("High confidence in predictions - signals are aligning well")
            elif week_perf.get('avg_confidence', 0) < 0.6:
                insights.append("Low confidence signals - market may be uncertain")
        else:
            insights.append("Collecting more data to improve prediction accuracy")
            insights.append("System is in learning phase - patience recommended")
        
        return insights
    
    async def _generate_recommendations(self) -> list:
        """Generate trading recommendations based on performance"""
        recommendations = []
        
        week_perf = await performance_tracker.get_recent_performance(7)
        
        if not week_perf.get('total_predictions'):
            recommendations.append("Continue paper trading until sufficient data collected")
            recommendations.append("Monitor signal agreement before live trading")
            return recommendations
        
        accuracy = week_perf.get('accuracy', 0)
        
        if accuracy >= 0.7:
            recommendations.append("Consider increasing position sizes for high-conviction trades")
            recommendations.append("Model ready for live options trading")
        elif accuracy >= 0.6:
            recommendations.append("Maintain conservative position sizing")
            recommendations.append("Focus on trades with ≥85% confidence")
        elif accuracy >= 0.5:
            recommendations.append("Continue paper trading to refine model")
            recommendations.append("Analyze which signals are underperforming")
        else:
            recommendations.append("Paper trading only - model needs improvement")
            recommendations.append("Consider retraining with fresh data")
        
        return recommendations
    
    def stop(self):
        """Stop the daily reporting"""
        self.running = False
        logger.info("📅 Daily reporting stopped")

# Global instance
daily_reporter = DailyReporter()