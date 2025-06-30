"""
Auto-discovery system for trading strategies
Prevents loss of strategy configurations during git operations
"""

import os
import importlib.util
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class StrategyConfig:
    name: str
    confidence_threshold: float
    min_signals_required: int
    position_size_pct: float
    description: str

def discover_all_strategies() -> Dict[str, StrategyConfig]:
    """Auto-discover all strategy configurations"""
    
    # Hardcoded base strategies (always available)
    base_strategies = {
        "conservative": StrategyConfig(
            name="Conservative",
            confidence_threshold=0.75,
            min_signals_required=4,
            position_size_pct=0.15,
            description="High confidence, multiple signal agreement, small positions"
        ),
        "moderate": StrategyConfig(
            name="Moderate", 
            confidence_threshold=0.60,
            min_signals_required=3,
            position_size_pct=0.20,
            description="Balanced approach with moderate risk"
        ),
        "aggressive": StrategyConfig(
            name="Aggressive",
            confidence_threshold=0.50,
            min_signals_required=2,
            position_size_pct=0.25,
            description="Lower threshold, larger positions, more trades"
        ),
        "scalping": StrategyConfig(
            name="Scalping",
            confidence_threshold=0.75,
            min_signals_required=3,
            position_size_pct=0.10,
            description="Fast 15min-2hr trades, high confidence, small positions"
        ),
        "swing": StrategyConfig(
            name="Swing",
            confidence_threshold=0.70,
            min_signals_required=3,
            position_size_pct=0.30,
            description="2-5 day holds, moderate confidence, larger positions"
        ),
        "momentum": StrategyConfig(
            name="Momentum",
            confidence_threshold=0.68,
            min_signals_required=2,
            position_size_pct=0.20,
            description="Trend following, momentum-based entries"
        ),
        "volatility": StrategyConfig(
            name="Volatility",
            confidence_threshold=0.73,
            min_signals_required=3,
            position_size_pct=0.25,
            description="IV expansion plays, volatility timing"
        ),
        "mean_reversion": StrategyConfig(
            name="Mean Reversion",
            confidence_threshold=0.72,
            min_signals_required=3,
            position_size_pct=0.22,
            description="Counter-trend, oversold/overbought plays"
        )
    }
    
    # TODO: Auto-discover from src/strategies/ directory
    # strategies_dir = "src/strategies"
    # if os.path.exists(strategies_dir):
    #     for file in os.listdir(strategies_dir):
    #         if file.endswith("_strategy.py"):
    #             strategy_name = file.replace("_strategy.py", "")
    #             # Load configuration from file
    
    return base_strategies

def get_strategy_list() -> List[str]:
    """Get list of all available strategy IDs"""
    return list(discover_all_strategies().keys())

if __name__ == "__main__":
    strategies = discover_all_strategies()
    print(f"📊 Discovered {len(strategies)} strategies:")
    for strategy_id, config in strategies.items():
        print(f"   • {strategy_id}: {config.name} ({config.confidence_threshold:.0%} threshold)")
