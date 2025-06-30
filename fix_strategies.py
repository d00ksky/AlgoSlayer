# Fix to add 5 missing strategies to multi_strategy_manager.py

import re

# Read the file
with open('src/core/multi_strategy_manager.py', 'r') as f:
    content = f.read()

# Find the aggressive strategy closing and replace
old_pattern = r'(\s+description=Lower threshold, larger positions, more trades\s+\)\s+}')"
new_content =  description=Lower threshold, larger positions, more trades
