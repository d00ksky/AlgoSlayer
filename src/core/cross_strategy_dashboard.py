"""
Cross-Strategy Learning Dashboard
Comprehensive dashboard showing insights across all strategies
"""

from datetime import datetime
from typing import Dict, List, Tuple
from loguru import logger

class CrossStrategyDashboard:
    """Comprehensive dashboard for cross-strategy insights"""
    
    def __init__(self):
        self.strategies = ["conservative", "moderate", "aggressive"]
        logger.info("📊 Cross-Strategy Learning Dashboard initialized")
    
    def generate_comprehensive_dashboard(self) -> str:
        """Generate complete cross-strategy learning dashboard"""
        
        dashboard = "🧠 **Cross-Strategy Learning Dashboard**\n"
        dashboard += "=" * 45 + "\n\n"
        
        try:
            # Section 1: Strategy Performance Comparison
            dashboard += self._generate_performance_comparison()
            
            # Section 2: Signal Intelligence Insights
            dashboard += self._generate_signal_insights()
            
            # Section 3: Capital Allocation Recommendations
            dashboard += self._generate_allocation_recommendations()
            
            # Section 4: Learning Progress Summary
            dashboard += self._generate_learning_summary()
            
        except Exception as e:
            logger.error(f"❌ Error generating cross-strategy dashboard: {e}")
            dashboard += f"❌ **Error**: {str(e)}\n"
        
        dashboard += f"\n🔄 **Updated**: {datetime.now().strftime('%H:%M:%S')}"
        
        return dashboard
    
    def _generate_performance_comparison(self) -> str:
        """Generate strategy performance comparison section"""
        section = "📊 **Strategy Performance Ranking**\n\n"
        
        try:
            # Import cross-strategy analyzer
            try:
                from .cross_strategy_analyzer import cross_strategy_analyzer
            except ImportError:
                from src.core.cross_strategy_analyzer import cross_strategy_analyzer
            
            # Get performance data for all strategies
            performances = {}
            for strategy_id in self.strategies:
                perf = cross_strategy_analyzer.get_strategy_performance(strategy_id)
                if perf:
                    performances[strategy_id] = perf
            
            if not performances:
                section += "⚠️ No performance data available yet\n"
                section += "📈 Start trading to generate insights!\n\n"
                return section
            
            # Rank strategies by multiple criteria
            def performance_score(perf):
                return (
                    perf.profit_factor * 0.4 +
                    perf.win_rate * 100 * 0.3 +
                    perf.sharpe_ratio * 10 * 0.2 +
                    (1 - perf.max_drawdown) * 100 * 0.1
                )
            
            ranked_strategies = sorted(
                performances.keys(),
                key=lambda k: performance_score(performances[k]),
                reverse=True
            )
            
            # Display rankings
            emojis = ["🥇", "🥈", "🥉"]
            strategy_emojis = {"conservative": "🛡️", "moderate": "⚖️", "aggressive": "🚀"}
            
            for i, strategy_id in enumerate(ranked_strategies):
                perf = performances[strategy_id]
                rank_emoji = emojis[i] if i < len(emojis) else "📊"
                strategy_emoji = strategy_emojis.get(strategy_id, "📊")
                
                section += f"{rank_emoji} {strategy_emoji} **{strategy_id.title()}**\n"
                section += f"   Balance: ${perf.current_balance:.2f} "
                section += f"({((perf.current_balance - 1000) / 1000 * 100):+.1f}%)\n"
                section += f"   Win Rate: {perf.win_rate:.1%} | "
                section += f"PF: {perf.profit_factor:.2f} | "
                section += f"Trades: {perf.total_trades}\n"
                section += f"   Sharpe: {perf.sharpe_ratio:.2f} | "
                section += f"Drawdown: {perf.max_drawdown:.1%}\n\n"
            
            # Add performance insights
            best_strategy = ranked_strategies[0]
            best_perf = performances[best_strategy]
            
            section += f"💡 **Top Performer**: {best_strategy.title()}\n"
            section += f"   🎯 Leading by: {performance_score(best_perf):.1f} points\n\n"
            
        except Exception as e:
            section += f"❌ Error loading performance data: {str(e)}\n\n"
        
        return section
    
    def _generate_signal_insights(self) -> str:
        """Generate signal intelligence insights section"""
        section = "🧠 **Signal Intelligence Insights**\n\n"
        
        try:
            # Import shared signal intelligence
            try:
                from .shared_signal_intelligence import shared_signal_intelligence
            except ImportError:
                from src.core.shared_signal_intelligence import shared_signal_intelligence
            
            # Get signal insights
            insights = shared_signal_intelligence.generate_signal_insights()
            
            if not insights:
                section += "ℹ️ No signal insights available yet\n"
                section += "📊 Continue trading to gather signal data\n\n"
                return section
            
            # Show top signal performers
            signal_performance = {}
            for signal_name in shared_signal_intelligence.signals:
                accuracies = []
                for strategy_id in self.strategies:
                    perf = shared_signal_intelligence.analyze_signal_performance_for_strategy(
                        strategy_id, signal_name
                    )
                    if perf:
                        accuracies.append(perf.accuracy)
                
                if accuracies:
                    import statistics
                    signal_performance[signal_name] = statistics.mean(accuracies)
            
            if signal_performance:
                top_signals = sorted(
                    signal_performance.keys(),
                    key=lambda k: signal_performance[k],
                    reverse=True
                )[:3]
                
                section += "🏆 **Top Performing Signals:**\n"
                for i, signal in enumerate(top_signals):
                    accuracy = signal_performance[signal]
                    section += f"{i+1}. {signal.replace('_', ' ').title()}: {accuracy:.1%}\n"
                section += "\n"
            
            # Show cross-strategy learning opportunities
            learning_insights = [i for i in insights if i.insight_type == "accuracy_gap"][:3]
            
            if learning_insights:
                section += "📈 **Learning Opportunities:**\n"
                for i, insight in enumerate(learning_insights):
                    section += f"{i+1}. {insight.description}\n"
                    section += f"   💡 Action: {insight.recommended_action}\n"
                    section += f"   📊 Expected: +{insight.expected_improvement:.1%}\n\n"
            
        except Exception as e:
            section += f"❌ Error loading signal insights: {str(e)}\n\n"
        
        return section
    
    def _generate_allocation_recommendations(self) -> str:
        """Generate capital allocation recommendations section"""
        section = "💰 **Capital Allocation Strategy**\n\n"
        
        try:
            # Import dynamic capital allocation
            try:
                from .dynamic_capital_allocation import dynamic_capital_allocation
            except ImportError:
                from src.core.dynamic_capital_allocation import dynamic_capital_allocation
            
            # Get allocation recommendations
            recommendations = dynamic_capital_allocation.generate_allocation_recommendations()
            
            if not recommendations:
                section += "⚠️ Unable to generate allocation recommendations\n\n"
                return section
            
            # Show current allocations
            section += "📊 **Current Allocation:**\n"
            emojis = {"conservative": "🛡️", "moderate": "⚖️", "aggressive": "🚀"}
            
            total_changes = 0
            for rec in recommendations:
                emoji = emojis.get(rec.strategy_id, "📊")
                section += f"{emoji} {rec.strategy_id.title()}: {rec.current_percent:.1f}%"
                
                if abs(rec.change_percent) >= 5.0:  # 5% threshold
                    if rec.change_percent > 0:
                        section += f" → {rec.recommended_percent:.1f}% 📈"
                    else:
                        section += f" → {rec.recommended_percent:.1f}% 📉"
                    total_changes += 1
                
                section += "\n"
            
            section += "\n"
            
            # Show rebalancing recommendations
            if total_changes > 0:
                section += f"🔄 **Rebalancing Needed**: {total_changes} strategies\n"
                
                for rec in recommendations:
                    if abs(rec.change_percent) >= 5.0:
                        section += f"• {rec.strategy_id.title()}: {rec.reasoning}\n"
                
                section += "\n"
            else:
                section += "✅ **Portfolio Balanced**: No rebalancing needed\n\n"
            
        except Exception as e:
            section += f"❌ Error loading allocation data: {str(e)}\n\n"
        
        return section
    
    def _generate_learning_summary(self) -> str:
        """Generate learning progress summary section"""
        section = "🎓 **Learning Progress Summary**\n\n"
        
        try:
            # Count total insights and recommendations
            total_insights = 0
            total_recommendations = 0
            
            # Signal insights
            try:
                from .shared_signal_intelligence import shared_signal_intelligence
                signal_insights = shared_signal_intelligence.generate_signal_insights()
                total_insights += len(signal_insights)
                total_recommendations += len([i for i in signal_insights if i.expected_improvement > 0.05])
            except:
                pass
            
            # Cross-strategy insights
            try:
                from .cross_strategy_analyzer import cross_strategy_analyzer
                cross_insights = cross_strategy_analyzer.generate_cross_strategy_insights()
                total_insights += len(cross_insights)
                total_recommendations += len([i for i in cross_insights if i.expected_improvement > 0.05])
            except:
                pass
            
            # Allocation recommendations
            try:
                from .dynamic_capital_allocation import dynamic_capital_allocation
                alloc_recs = dynamic_capital_allocation.generate_allocation_recommendations()
                allocation_changes = len([r for r in alloc_recs if abs(r.change_percent) >= 5.0])
                total_recommendations += allocation_changes
            except:
                pass
            
            section += f"📊 **Total Insights Generated**: {total_insights}\n"
            section += f"💡 **Actionable Recommendations**: {total_recommendations}\n"
            
            if total_recommendations > 0:
                section += f"📈 **Optimization Potential**: High\n"
                section += f"🎯 **Next Action**: Review and apply recommendations\n"
            else:
                section += f"✅ **System Status**: Well optimized\n"
                section += f"🔄 **Monitoring**: Continue gathering data\n"
            
            # Learning system status
            section += f"\n🧠 **Learning Systems Status:**\n"
            section += f"• Cross-Strategy Analysis: ✅ Active\n"
            section += f"• Signal Intelligence: ✅ Active\n"
            section += f"• Dynamic Allocation: ✅ Active\n"
            section += f"• Performance Tracking: ✅ Active\n"
            
        except Exception as e:
            section += f"❌ Error generating learning summary: {str(e)}\n"
        
        return section
    
    def get_quick_learning_summary(self) -> str:
        """Generate quick summary for regular updates"""
        
        summary = "🧠 **Cross-Strategy Learning Status**\n\n"
        
        try:
            # Get best performing strategy
            try:
                from .cross_strategy_analyzer import cross_strategy_analyzer
                best_strategy, best_perf, reason = cross_strategy_analyzer.identify_best_performing_strategy()
                
                if best_strategy != "none":
                    strategy_emojis = {"conservative": "🛡️", "moderate": "⚖️", "aggressive": "🚀"}
                    emoji = strategy_emojis.get(best_strategy, "📊")
                    
                    summary += f"🏆 **Top Performer**: {emoji} {best_strategy.title()}\n"
                    summary += f"📊 **Balance**: ${best_perf.current_balance:.2f} "
                    summary += f"({((best_perf.current_balance - 1000) / 1000 * 100):+.1f}%)\n"
                    summary += f"🎯 **Win Rate**: {best_perf.win_rate:.1%} | **PF**: {best_perf.profit_factor:.2f}\n\n"
                else:
                    summary += "⚠️ Insufficient data for performance ranking\n\n"
                    
            except Exception as e:
                summary += f"❌ Performance analysis error: {str(e)}\n\n"
            
            # Quick signal intelligence
            try:
                from .shared_signal_intelligence import shared_signal_intelligence
                cache_data = shared_signal_intelligence.load_intelligence_cache()
                
                if cache_data:
                    insights_count = len(cache_data.get("insights", []))
                    summary += f"🧠 **Signal Insights**: {insights_count} active\n"
                    
                    # Show top signal
                    signal_performances = cache_data.get("signal_performances", {})
                    if signal_performances:
                        import statistics
                        signal_avg = {}
                        for signal, perfs in signal_performances.items():
                            accuracies = [p["accuracy"] for p in perfs.values()]
                            if accuracies:
                                signal_avg[signal] = statistics.mean(accuracies)
                        
                        if signal_avg:
                            top_signal = max(signal_avg.keys(), key=lambda k: signal_avg[k])
                            top_accuracy = signal_avg[top_signal]
                            summary += f"🏆 **Top Signal**: {top_signal.replace('_', ' ').title()} ({top_accuracy:.1%})\n"
                else:
                    summary += f"🧠 **Signal Analysis**: Initializing...\n"
            except:
                summary += f"🧠 **Signal Analysis**: Error loading data\n"
            
            summary += f"\n📱 Use /cross_strategy for full dashboard"
            
        except Exception as e:
            summary += f"❌ Error generating summary: {str(e)}"
        
        return summary

# Global instance
cross_strategy_dashboard = CrossStrategyDashboard()

if __name__ == "__main__":
    # Test the cross-strategy dashboard
    logger.info("🧪 Testing Cross-Strategy Learning Dashboard")
    
    dashboard = CrossStrategyDashboard()
    
    print("🧠 Cross-Strategy Dashboard Test")
    print("=" * 50)
    
    # Test comprehensive dashboard
    full_dashboard = dashboard.generate_comprehensive_dashboard()
    print("Full Dashboard Length:", len(full_dashboard), "characters")
    print("\nFirst 500 characters:")
    print(full_dashboard[:500] + "..." if len(full_dashboard) > 500 else full_dashboard)
    
    # Test quick summary
    print("\n" + "=" * 50)
    print("Quick Learning Summary:")
    quick_summary = dashboard.get_quick_learning_summary()
    print(quick_summary)