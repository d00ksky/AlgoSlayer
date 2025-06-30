# Quick fix for multi_strategy_manager.py
import re

# Read the file
with open('src/core/multi_strategy_manager.py', 'r') as f:
    content = f.read()

# Replace the strategy_configs section
old_section = '''        # Define the three strategies
        self.strategy_configs = {
            conservative: StrategyConfig(
                name=Conservative,
                confidence_threshold=0.75,
                min_signals_required=4,
                position_size_pct=0.15,
                description=High confidence, multiple signal agreement, small positions
            ),
            moderate: StrategyConfig(
                name=Moderate,
                confidence_threshold=0.60,
                min_signals_required=3,
                position_size_pct=0.20,
                description=Balanced approach with moderate risk
            ),
            aggressive: StrategyConfig(
                name=Aggressive,
                confidence_threshold=0.50,
                min_signals_required=2,
                position_size_pct=0.25,
                description=Lower threshold, larger positions, more trades
            )
        }'''

new_section = '''        # Auto-discover all strategies
        from .strategy_auto_discovery import discover_all_strategies
        self.strategy_configs = discover_all_strategies()'''

# Replace
content = content.replace(old_section, new_section)

# Write back
with open('src/core/multi_strategy_manager.py', 'w') as f:
    f.write(content)

print("Success: Updated multi_strategy_manager.py to use auto-discovery")
