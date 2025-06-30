"""
Adaptive Learning System for Options Trading
Learns from actual options trading outcomes to improve signal weights and strategy
Provides real-time learning and adaptation based on P&L performance
"""
import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
import os

class AdaptiveLearningSystem:
    """Real-time learning system for options trading improvement"""
    
    def __init__(self, db_path: str = "data/options_performance.db"):
        self.db_path = db_path
        self.min_trades_for_learning = 5  # Minimum trades to start learning
        self.learning_rate = 0.1  # How quickly to adapt
        
    def analyze_signal_performance(self) -> Dict[str, Any]:
        """Analyze which signals contribute to profitable trades"""
        
        logger.info("🧠 Analyzing signal performance for adaptive learning...")
        
        if not os.path.exists(self.db_path):
            return {'error': 'No trading database found'}
        
        conn = sqlite3.connect(self.db_path)
        
        # Get all completed trades with signals data
        query = """
        SELECT 
            p.prediction_id,
            p.confidence,
            p.signals_data,
            o.net_pnl,
            o.pnl_percentage,
            o.exit_reason
        FROM options_predictions p
        INNER JOIN options_outcomes o ON p.prediction_id = o.prediction_id
        WHERE p.signals_data IS NOT NULL 
        AND p.signals_data != '{}' 
        AND p.signals_data != ''
        ORDER BY p.timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            logger.warning("⚠️ No trades with signals data found")
            return {'error': 'No signals data available for learning'}
        
        logger.info(f"📊 Analyzing {len(df)} trades with signals data")
        
        # Parse signals data and analyze performance
        signal_performance = {}
        signal_names = set()
        
        for _, row in df.iterrows():
            try:
                signals_data = json.loads(row['signals_data'])
                is_profitable = row['net_pnl'] > 0
                pnl_pct = row['pnl_percentage']
                
                # Analyze each signal's contribution
                for signal_name, signal_info in signals_data.items():
                    signal_names.add(signal_name)
                    
                    if signal_name not in signal_performance:
                        signal_performance[signal_name] = {
                            'trades': [],
                            'profitable_trades': 0,
                            'total_trades': 0,
                            'total_pnl': 0.0,
                            'avg_confidence': 0.0,
                            'directions': {'BUY': 0, 'SELL': 0, 'HOLD': 0}
                        }
                    
                    perf = signal_performance[signal_name]
                    direction = signal_info.get('direction', 'HOLD')
                    confidence = signal_info.get('confidence', 0.5)
                    
                    # Convert percentage to decimal if needed
                    if confidence > 1:
                        confidence = confidence / 100.0
                    
                    perf['trades'].append({
                        'direction': direction,
                        'confidence': confidence,
                        'profitable': is_profitable,
                        'pnl_pct': pnl_pct
                    })
                    
                    perf['total_trades'] += 1
                    perf['directions'][direction] += 1
                    perf['total_pnl'] += pnl_pct
                    perf['avg_confidence'] += confidence
                    
                    if is_profitable:
                        perf['profitable_trades'] += 1
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"⚠️ Error parsing signals data: {e}")
                continue
        
        # Calculate final metrics
        for signal_name, perf in signal_performance.items():
            if perf['total_trades'] > 0:
                perf['win_rate'] = perf['profitable_trades'] / perf['total_trades']
                perf['avg_pnl_pct'] = perf['total_pnl'] / perf['total_trades']
                perf['avg_confidence'] = perf['avg_confidence'] / perf['total_trades']
                
                # Calculate direction effectiveness
                profitable_by_direction = {}
                for trade in perf['trades']:
                    direction = trade['direction']
                    if direction not in profitable_by_direction:
                        profitable_by_direction[direction] = {'profitable': 0, 'total': 0}
                    
                    profitable_by_direction[direction]['total'] += 1
                    if trade['profitable']:
                        profitable_by_direction[direction]['profitable'] += 1
                
                perf['direction_effectiveness'] = {}
                for direction, stats in profitable_by_direction.items():
                    if stats['total'] > 0:
                        perf['direction_effectiveness'][direction] = stats['profitable'] / stats['total']
                
                # Calculate overall signal score (combines win rate and average P&L)
                perf['signal_score'] = (perf['win_rate'] * 0.6) + (min(perf['avg_pnl_pct'], 1.0) * 0.4)
        
        return {
            'signal_performance': signal_performance,
            'total_trades_analyzed': len(df),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def generate_adaptive_weights(self, current_weights: Dict[str, float]) -> Dict[str, float]:
        """Generate new signal weights based on performance analysis"""
        
        logger.info("⚖️ Generating adaptive signal weights...")
        
        analysis = self.analyze_signal_performance()
        
        if 'error' in analysis:
            logger.warning(f"⚠️ Cannot adapt weights: {analysis['error']}")
            return current_weights
        
        signal_performance = analysis['signal_performance']
        
        if len(signal_performance) == 0:
            logger.warning("⚠️ No signal performance data available")
            return current_weights
        
        new_weights = current_weights.copy()
        
        # Calculate adaptive adjustments
        for signal_name, perf in signal_performance.items():
            if signal_name not in current_weights:
                continue
            
            current_weight = current_weights[signal_name]
            
            # Only adjust if we have enough data
            if perf['total_trades'] < 3:
                continue
            
            # Calculate performance score (0 to 1)
            signal_score = perf['signal_score']
            
            # Calculate adjustment factor
            # Good performance (score > 0.6) increases weight
            # Poor performance (score < 0.4) decreases weight
            if signal_score > 0.6:
                adjustment = (signal_score - 0.6) * self.learning_rate * 2
                new_weight = current_weight * (1 + adjustment)
            elif signal_score < 0.4:
                adjustment = (0.4 - signal_score) * self.learning_rate * 2
                new_weight = current_weight * (1 - adjustment)
            else:
                new_weight = current_weight  # Neutral performance
            
            # Apply bounds (weights between 0.02 and 0.25)
            new_weight = max(0.02, min(0.25, new_weight))
            new_weights[signal_name] = new_weight
            
            logger.info(f"📊 {signal_name}: {current_weight:.3f} → {new_weight:.3f} "
                       f"(score: {signal_score:.2f}, trades: {perf['total_trades']})")
        
        # Normalize weights to sum to 1.0
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            for signal_name in new_weights:
                new_weights[signal_name] = new_weights[signal_name] / total_weight
        
        return new_weights
    
    def identify_learning_opportunities(self) -> List[Dict[str, Any]]:
        """Identify specific areas for improvement"""
        
        logger.info("🔍 Identifying learning opportunities...")
        
        analysis = self.analyze_signal_performance()
        
        if 'error' in analysis:
            return []
        
        opportunities = []
        signal_performance = analysis['signal_performance']
        
        # Identify underperforming signals
        for signal_name, perf in signal_performance.items():
            if perf['total_trades'] >= 3:
                
                # Low win rate signals
                if perf['win_rate'] < 0.3:
                    opportunities.append({
                        'type': 'underperforming_signal',
                        'signal': signal_name,
                        'issue': f"Low win rate: {perf['win_rate']:.1%}",
                        'recommendation': "Consider reducing weight or investigating signal logic",
                        'severity': 'high' if perf['win_rate'] < 0.2 else 'medium'
                    })
                
                # Negative average P&L
                if perf['avg_pnl_pct'] < -0.2:
                    opportunities.append({
                        'type': 'negative_pnl_signal',
                        'signal': signal_name,
                        'issue': f"Avg P&L: {perf['avg_pnl_pct']:.1%}",
                        'recommendation': "This signal may be counterproductive",
                        'severity': 'high'
                    })
                
                # Direction inconsistency
                directions = perf['direction_effectiveness']
                if len(directions) > 1:
                    direction_scores = list(directions.values())
                    if max(direction_scores) - min(direction_scores) > 0.4:
                        best_direction = max(directions.items(), key=lambda x: x[1])
                        opportunities.append({
                            'type': 'direction_bias',
                            'signal': signal_name,
                            'issue': f"Strong directional bias toward {best_direction[0]}",
                            'recommendation': f"Consider weighting {best_direction[0]} signals higher",
                            'severity': 'low'
                        })
        
        # Identify high-performing signals
        top_signals = sorted(signal_performance.items(), 
                           key=lambda x: x[1]['signal_score'], reverse=True)[:3]
        
        for signal_name, perf in top_signals:
            if perf['signal_score'] > 0.7 and perf['total_trades'] >= 3:
                opportunities.append({
                    'type': 'high_performer',
                    'signal': signal_name,
                    'issue': f"Excellent performance: {perf['signal_score']:.2f} score",
                    'recommendation': "Consider increasing weight for this signal",
                    'severity': 'positive'
                })
        
        return opportunities
    
    def generate_strategy_recommendations(self) -> List[str]:
        """Generate high-level strategy recommendations"""
        
        analysis = self.analyze_signal_performance()
        
        if 'error' in analysis:
            return ["Insufficient data for strategy recommendations"]
        
        recommendations = []
        signal_performance = analysis['signal_performance']
        total_trades = analysis['total_trades_analyzed']
        
        # Overall performance analysis
        if total_trades >= 5:
            profitable_signals = sum(1 for perf in signal_performance.values() 
                                   if perf['win_rate'] > 0.5)
            total_signals = len(signal_performance)
            
            if profitable_signals / total_signals < 0.5:
                recommendations.append("📉 Most signals underperforming - consider raising confidence threshold")
                recommendations.append("🎯 Focus on 3-5 best performing signals only")
            
            # Check for consistent losers
            consistent_losers = [name for name, perf in signal_performance.items()
                               if perf['total_trades'] >= 3 and perf['win_rate'] < 0.2]
            
            if consistent_losers:
                recommendations.append(f"❌ Consider disabling: {', '.join(consistent_losers)}")
            
            # Check for overconfidence
            avg_confidence = np.mean([perf['avg_confidence'] for perf in signal_performance.values()])
            overall_win_rate = np.mean([perf['win_rate'] for perf in signal_performance.values()])
            
            if avg_confidence > 0.8 and overall_win_rate < 0.4:
                recommendations.append("⚠️ Signals overconfident - implement confidence calibration")
        
        # Data collection recommendations
        if total_trades < 10:
            recommendations.append("📊 Collect more trading data (target: 20+ trades)")
            recommendations.append("🕐 Run system for 2-4 weeks in paper trading mode")
        
        # Signal-specific recommendations
        opportunities = self.identify_learning_opportunities()
        high_priority = [opp for opp in opportunities if opp['severity'] == 'high']
        
        if high_priority:
            recommendations.append("🚨 Address high-priority signal issues first")
            for opp in high_priority[:3]:  # Top 3 issues
                recommendations.append(f"   • {opp['signal']}: {opp['recommendation']}")
        
        return recommendations
    
    def create_learning_summary(self) -> Dict[str, Any]:
        """Create comprehensive learning summary"""
        
        logger.info("📋 Creating comprehensive learning summary...")
        
        analysis = self.analyze_signal_performance()
        
        if 'error' in analysis:
            return {'error': analysis['error']}
        
        opportunities = self.identify_learning_opportunities()
        recommendations = self.generate_strategy_recommendations()
        
        # Performance metrics
        signal_performance = analysis['signal_performance']
        
        if signal_performance:
            overall_win_rate = np.mean([perf['win_rate'] for perf in signal_performance.values()])
            overall_avg_pnl = np.mean([perf['avg_pnl_pct'] for perf in signal_performance.values()])
            
            best_signal = max(signal_performance.items(), key=lambda x: x[1]['signal_score'])
            worst_signal = min(signal_performance.items(), key=lambda x: x[1]['signal_score'])
        else:
            overall_win_rate = 0
            overall_avg_pnl = 0
            best_signal = None
            worst_signal = None
        
        summary = {
            'analysis_timestamp': datetime.now().isoformat(),
            'trades_analyzed': analysis['total_trades_analyzed'],
            'signals_analyzed': len(signal_performance),
            
            'performance_metrics': {
                'overall_win_rate': overall_win_rate,
                'overall_avg_pnl_pct': overall_avg_pnl,
                'best_signal': best_signal[0] if best_signal else None,
                'best_signal_score': best_signal[1]['signal_score'] if best_signal else 0,
                'worst_signal': worst_signal[0] if worst_signal else None,
                'worst_signal_score': worst_signal[1]['signal_score'] if worst_signal else 0
            },
            
            'learning_opportunities': opportunities,
            'strategy_recommendations': recommendations,
            'signal_performance_detail': signal_performance,
            
            'learning_status': self._assess_learning_status(analysis['total_trades_analyzed'])
        }
        
        return summary
    
    def _assess_learning_status(self, total_trades: int) -> str:
        """Assess the current learning status of the system"""
        
        if total_trades < 5:
            return "INSUFFICIENT_DATA - Need more trades for meaningful learning"
        elif total_trades < 10:
            return "EARLY_LEARNING - Basic patterns emerging"
        elif total_trades < 20:
            return "MODERATE_LEARNING - Reliable patterns developing"
        else:
            return "MATURE_LEARNING - Strong statistical significance"
    
    def print_learning_summary(self, summary: Dict[str, Any]):
        """Print formatted learning summary"""
        
        print("=" * 80)
        print("🧠 ADAPTIVE LEARNING SYSTEM REPORT")
        print("=" * 80)
        
        if 'error' in summary:
            print(f"❌ Error: {summary['error']}")
            return
        
        metrics = summary['performance_metrics']
        
        print(f"\n📊 LEARNING STATUS: {summary['learning_status']}")
        print(f"   Trades Analyzed: {summary['trades_analyzed']}")
        print(f"   Signals Analyzed: {summary['signals_analyzed']}")
        
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"   Overall Win Rate: {metrics['overall_win_rate']:.1%}")
        print(f"   Overall Avg P&L: {metrics['overall_avg_pnl_pct']:.1%}")
        
        if metrics['best_signal']:
            print(f"   🏆 Best Signal: {metrics['best_signal']} (score: {metrics['best_signal_score']:.2f})")
            print(f"   ⚠️ Worst Signal: {metrics['worst_signal']} (score: {metrics['worst_signal_score']:.2f})")
        
        # Learning opportunities
        opportunities = summary['learning_opportunities']
        high_priority = [opp for opp in opportunities if opp['severity'] == 'high']
        
        if high_priority:
            print(f"\n🚨 HIGH PRIORITY ISSUES ({len(high_priority)}):")
            for opp in high_priority:
                print(f"   • {opp['signal']}: {opp['issue']}")
                print(f"     → {opp['recommendation']}")
        
        # Top recommendations
        recommendations = summary['strategy_recommendations']
        print(f"\n🎯 KEY RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. {rec}")
        
        # Signal performance summary
        signal_perf = summary['signal_performance_detail']
        if signal_perf:
            print(f"\n📊 TOP PERFORMING SIGNALS:")
            sorted_signals = sorted(signal_perf.items(), 
                                  key=lambda x: x[1]['signal_score'], reverse=True)
            
            for signal_name, perf in sorted_signals[:5]:
                print(f"   • {signal_name}: {perf['win_rate']:.1%} win rate, "
                      f"{perf['avg_pnl_pct']:.1%} avg P&L ({perf['total_trades']} trades)")
        
        print("=" * 80)

# Create global instance
adaptive_learning_system = AdaptiveLearningSystem()

if __name__ == "__main__":
    # Run adaptive learning analysis
    learning_system = AdaptiveLearningSystem()
    summary = learning_system.create_learning_summary()
    
    if 'error' in summary:
        print(f"❌ Error: {summary['error']}")
    else:
        learning_system.print_learning_summary(summary)
        
        # Test adaptive weight generation
        current_weights = {
            "news_sentiment": 0.10,
            "technical_analysis": 0.12,
            "options_flow": 0.12,
            "momentum": 0.08
        }
        
        print("\n🔄 Testing adaptive weight generation...")
        new_weights = learning_system.generate_adaptive_weights(current_weights)
        print("New weights:", new_weights)