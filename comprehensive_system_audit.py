#!/usr/bin/env python3
"""
Comprehensive System Audit
Checks every component of the AlgoSlayer trading system
"""
import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append('.')

async def audit_system():
    """Complete system audit"""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "components": {},
        "issues": [],
        "recommendations": []
    }
    
    print("=" * 60)
    print("ALGOSLAYER COMPREHENSIVE SYSTEM AUDIT")
    print("=" * 60)
    
    # 1. Check Configuration
    print("\n1. CONFIGURATION CHECK")
    print("-" * 40)
    try:
        from config.trading_config import config, TradingModeConfig
        TradingModeConfig.load_from_env()
        
        results["components"]["config"] = {
            "status": "OK",
            "mode": TradingModeConfig.get_mode_description(),
            "trading_enabled": TradingModeConfig.TRADING_ENABLED,
            "paper_trading": TradingModeConfig.PAPER_TRADING
        }
        print(f"✅ Configuration loaded")
        print(f"   Mode: {TradingModeConfig.get_mode_description()}")
    except Exception as e:
        results["components"]["config"] = {"status": "FAILED", "error": str(e)}
        results["issues"].append(f"Config error: {e}")
        print(f"❌ Configuration failed: {e}")
    
    # 2. Check Databases
    print("\n2. DATABASE CHECK")
    print("-" * 40)
    import sqlite3
    
    db_status = {}
    strategies = ['conservative', 'moderate', 'aggressive', 'scalping', 'swing', 'momentum', 'volatility', 'mean_reversion']
    
    for strategy in strategies:
        try:
            db_path = f'data/options_performance_{strategy}.db'
            if Path(db_path).exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get prediction count
                cursor.execute('SELECT COUNT(*) FROM options_predictions')
                pred_count = cursor.fetchone()[0]
                
                # Get last prediction date
                cursor.execute('SELECT MAX(timestamp) FROM options_predictions')
                last_pred = cursor.fetchone()[0]
                
                # Get outcomes
                cursor.execute('SELECT COUNT(*) FROM options_outcomes')
                outcomes = cursor.fetchone()[0]
                
                conn.close()
                
                db_status[strategy] = {
                    "predictions": pred_count,
                    "outcomes": outcomes,
                    "last_prediction": last_pred,
                    "status": "OK"
                }
                
                days_since = "Never"
                if last_pred:
                    last_date = datetime.strptime(last_pred, "%Y-%m-%d %H:%M:%S")
                    days_since = (datetime.now() - last_date).days
                
                print(f"  {strategy:15} - Preds: {pred_count:3}, Trades: {outcomes:3}, Last: {days_since} days ago")
            else:
                db_status[strategy] = {"status": "NO_DB"}
                print(f"  {strategy:15} - No database found")
                
        except Exception as e:
            db_status[strategy] = {"status": "ERROR", "error": str(e)}
            print(f"  {strategy:15} - Error: {e}")
    
    results["components"]["databases"] = db_status
    
    # 3. Check Signals
    print("\n3. SIGNAL CHECK")
    print("-" * 40)
    
    signal_results = {}
    signals_to_test = [
        'news_sentiment', 'technical_analysis', 'options_flow', 'volatility_analysis',
        'momentum', 'sector_correlation', 'mean_reversion', 'market_regime',
        'rtx_earnings', 'options_iv_percentile', 'defense_contract', 'trump_geopolitical'
    ]
    
    for signal_name in signals_to_test:
        try:
            # Import the signal class
            if signal_name == 'news_sentiment':
                from src.signals.news_sentiment_signal import NewsSentimentSignal
                signal = NewsSentimentSignal()
            elif signal_name == 'technical_analysis':
                from src.signals.technical_analysis_signal import TechnicalAnalysisSignal
                signal = TechnicalAnalysisSignal()
            elif signal_name == 'options_flow':
                from src.signals.options_flow_signal import OptionsFlowSignal
                signal = OptionsFlowSignal()
            elif signal_name == 'volatility_analysis':
                from src.signals.volatility_analysis_signal import VolatilityAnalysisSignal
                signal = VolatilityAnalysisSignal()
            elif signal_name == 'momentum':
                from src.signals.momentum_signal import MomentumSignal
                signal = MomentumSignal()
            elif signal_name == 'sector_correlation':
                from src.signals.sector_correlation_signal import SectorCorrelationSignal
                signal = SectorCorrelationSignal()
            elif signal_name == 'mean_reversion':
                from src.signals.mean_reversion_signal import MeanReversionSignal
                signal = MeanReversionSignal()
            elif signal_name == 'market_regime':
                from src.signals.market_regime_signal import MarketRegimeSignal
                signal = MarketRegimeSignal()
            elif signal_name == 'rtx_earnings':
                from src.signals.rtx_earnings_signal import RTXEarningsSignal
                signal = RTXEarningsSignal()
            elif signal_name == 'options_iv_percentile':
                from src.signals.options_iv_percentile_signal import OptionsIVPercentileSignal
                signal = OptionsIVPercentileSignal()
            elif signal_name == 'defense_contract':
                from src.signals.defense_contract_signal import DefenseContractSignal
                signal = DefenseContractSignal()
            elif signal_name == 'trump_geopolitical':
                from src.signals.trump_geopolitical_signal import TrumpGeopoliticalSignal
                signal = TrumpGeopoliticalSignal()
            else:
                continue
            
            # Test the signal
            result = await signal.analyze('RTX')
            
            if result and 'direction' in result and 'confidence' in result:
                signal_results[signal_name] = {
                    "status": "OK",
                    "direction": result.get('direction'),
                    "confidence": result.get('confidence')
                }
                print(f"  ✅ {signal_name:25} - {result.get('direction'):4} @ {result.get('confidence'):.1%}")
            else:
                signal_results[signal_name] = {"status": "INCOMPLETE", "result": str(result)}
                print(f"  ⚠️  {signal_name:25} - Incomplete result")
                results["issues"].append(f"Signal {signal_name} returns incomplete data")
                
        except Exception as e:
            signal_results[signal_name] = {"status": "ERROR", "error": str(e)}
            print(f"  ❌ {signal_name:25} - Error: {str(e)[:50]}")
            results["issues"].append(f"Signal {signal_name} failed: {e}")
    
    results["components"]["signals"] = signal_results
    
    # 4. Check Signal Fusion
    print("\n4. SIGNAL FUSION CHECK")
    print("-" * 40)
    try:
        from src.core.signal_fusion import SignalFusionEngine
        fusion = SignalFusionEngine()
        decision = await fusion.make_trading_decision('RTX')
        fusion_dict = decision.to_dict()
        
        results["components"]["signal_fusion"] = {
            "status": "OK",
            "direction": fusion_dict.get("direction"),
            "confidence": fusion_dict.get("confidence"),
            "actionable_signals": len([s for s in fusion_dict.get("signals_data", {}).get("signals", []) if s.get("direction") != "HOLD"])
        }
        print(f"✅ Signal Fusion working")
        print(f"   Direction: {fusion_dict.get('direction')}, Confidence: {fusion_dict.get('confidence'):.1%}")
    except Exception as e:
        results["components"]["signal_fusion"] = {"status": "ERROR", "error": str(e)}
        results["issues"].append(f"Signal fusion failed: {e}")
        print(f"❌ Signal Fusion failed: {e}")
    
    # 5. Check Options Data Engine
    print("\n5. OPTIONS DATA ENGINE CHECK")
    print("-" * 40)
    try:
        from src.core.options_data_engine import OptionsDataEngine
        engine = OptionsDataEngine()
        
        # Get current price
        current_price = await engine.get_current_price('RTX')
        
        # Get options chain
        chain = await engine.get_options_chain('RTX')
        
        if chain:
            call_count = len([o for o in chain if o.get('type') == 'call'])
            put_count = len([o for o in chain if o.get('type') == 'put'])
            
            results["components"]["options_engine"] = {
                "status": "OK",
                "current_price": current_price,
                "calls": call_count,
                "puts": put_count
            }
            print(f"✅ Options Data Engine working")
            print(f"   RTX Price: ${current_price:.2f}")
            print(f"   Options: {call_count} calls, {put_count} puts")
        else:
            results["components"]["options_engine"] = {"status": "NO_DATA"}
            print(f"⚠️  No options data available")
            
    except Exception as e:
        results["components"]["options_engine"] = {"status": "ERROR", "error": str(e)}
        results["issues"].append(f"Options engine failed: {e}")
        print(f"❌ Options Data Engine failed: {e}")
    
    # 6. Check ML Models
    print("\n6. ML SYSTEM CHECK")
    print("-" * 40)
    ml_models_path = Path('/opt/rtx-trading/ml_models')
    trained_models_path = Path('trained_models')
    
    if ml_models_path.exists():
        models = list(ml_models_path.glob('*.pkl'))
        print(f"  Server models: {len(models)} found")
        for model in models[:3]:
            print(f"    - {model.name}")
    else:
        print(f"  Server models: Directory not found")
        
    if trained_models_path.exists():
        models = list(trained_models_path.glob('*.pkl'))
        print(f"  Local models: {len(models)} found")
        for model in models[:3]:
            print(f"    - {model.name}")
    
    # 7. Check Schedulers
    print("\n7. SCHEDULER CHECK")
    print("-" * 40)
    try:
        from src.core.parallel_strategy_runner import ParallelStrategyRunner
        runner = ParallelStrategyRunner()
        
        scheduler_status = {}
        for strategy_id in runner.strategies.keys():
            strategy = runner.strategies[strategy_id]
            scheduler_status[strategy_id] = {
                "has_scheduler": hasattr(strategy, 'scheduler'),
                "balance": strategy.balance if hasattr(strategy, 'balance') else 0
            }
            print(f"  {strategy_id:15} - Balance: ${strategy.balance:.2f}")
            
        results["components"]["schedulers"] = scheduler_status
        
    except Exception as e:
        results["components"]["schedulers"] = {"status": "ERROR", "error": str(e)}
        print(f"❌ Scheduler check failed: {e}")
    
    # 8. Generate Summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    
    # Count issues
    critical_issues = 0
    warnings = 0
    
    for component, data in results["components"].items():
        if isinstance(data, dict) and data.get("status") == "ERROR":
            critical_issues += 1
        elif isinstance(data, dict) and data.get("status") in ["INCOMPLETE", "NO_DATA"]:
            warnings += 1
    
    print(f"\n📊 Components Checked: {len(results['components'])}")
    print(f"❌ Critical Issues: {critical_issues}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"📝 Total Issues Found: {len(results['issues'])}")
    
    # Main issues
    if results["issues"]:
        print("\n🔴 CRITICAL ISSUES:")
        for issue in results["issues"][:5]:
            print(f"  • {issue}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    # Check if trading has stopped
    last_trade_days = 999
    for strategy, data in results["components"].get("databases", {}).items():
        if data.get("last_prediction"):
            last_date = datetime.strptime(data["last_prediction"], "%Y-%m-%d %H:%M:%S")
            days = (datetime.now() - last_date).days
            last_trade_days = min(last_trade_days, days)
    
    if last_trade_days > 7:
        print(f"  1. No trades in {last_trade_days} days - system appears stuck")
        print(f"     → Restart the service: systemctl restart rtx-trading")
        results["recommendations"].append("Restart service - no recent trades")
    
    if critical_issues > 0:
        print(f"  2. Fix {critical_issues} critical component failures")
        print(f"     → Check signal code for 'direction' variable errors")
        results["recommendations"].append("Fix signal code errors")
    
    # Save results
    with open('audit_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Full audit results saved to: audit_results.json")
    
    return results

if __name__ == "__main__":
    # Suppress INFO logs for cleaner output
    import logging
    logging.getLogger().setLevel(logging.WARNING)
    
    # Run audit
    asyncio.run(audit_system())