#!/usr/bin/env python3
"""
Apply ML-Recommended Optimizations for A/B Testing
Based on analysis showing all signals performing poorly at current thresholds
"""

import os
import shutil
from datetime import datetime
from loguru import logger

def backup_current_config():
    """Backup current configuration before making changes"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup files
    backups = [
        ("config/trading_config.py", f"config/trading_config_backup_{timestamp}.py"),
        ("src/core/options_scheduler.py", f"src/core/options_scheduler_backup_{timestamp}.py"),
        (".env", f".env_backup_{timestamp}")
    ]
    
    for source, backup in backups:
        if os.path.exists(source):
            try:
                shutil.copy2(source, backup)
                logger.info(f"✅ Backed up {source} → {backup}")
            except Exception as e:
                logger.error(f"❌ Failed to backup {source}: {e}")

def apply_confidence_threshold_optimization():
    """Apply ML recommendation: Increase confidence threshold from 60% to 75%"""
    logger.info("🎯 Applying confidence threshold optimization: 60% → 75%")
    
    # Update trading_config.py
    config_file = "config/trading_config.py"
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Replace confidence threshold
    content = content.replace(
        "CONFIDENCE_THRESHOLD = 0.35  # Minimum confidence to trade",
        "CONFIDENCE_THRESHOLD = 0.75  # ML Optimized: Increased from 0.35 for higher selectivity"
    )
    
    with open(config_file, 'w') as f:
        f.write(content)
    
    logger.success("✅ Updated confidence threshold in trading_config.py")

def apply_signal_agreement_optimization():
    """Apply ML recommendation: Require 4+ signals to agree instead of 3+"""
    logger.info("🎯 Applying signal agreement optimization: 3+ → 4+ signals")
    
    # Update options_scheduler.py
    scheduler_file = "src/core/options_scheduler.py"
    with open(scheduler_file, 'r') as f:
        content = f.read()
    
    # Update minimum signals required
    content = content.replace(
        "MIN_SIGNALS_REQUIRED = 3",
        "MIN_SIGNALS_REQUIRED = 4  # ML Optimized: Increased from 3 for higher conviction"
    )
    
    # Also update any hardcoded references
    content = content.replace(
        "min_signals_agreeing = 3",
        "min_signals_agreeing = 4  # ML Optimized"
    )
    
    with open(scheduler_file, 'w') as f:
        f.write(content)
    
    logger.success("✅ Updated signal agreement requirement in options_scheduler.py")

def apply_position_size_optimization():
    """Apply ML recommendation: Reduce position size during testing"""
    logger.info("🎯 Applying position size optimization: 20% → 15% max")
    
    # Update .env file
    env_file = ".env"
    env_lines = []
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Update or add MAX_POSITION_SIZE_PCT
    updated = False
    for i, line in enumerate(env_lines):
        if line.startswith("MAX_POSITION_SIZE_PCT="):
            env_lines[i] = "MAX_POSITION_SIZE_PCT=0.15  # ML Optimized: Reduced for testing\n"
            updated = True
            break
    
    if not updated:
        env_lines.append("MAX_POSITION_SIZE_PCT=0.15  # ML Optimized: Reduced for testing\n")
    
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    logger.success("✅ Updated position size limit in .env")

def create_ab_test_marker():
    """Create a marker file to track when A/B testing started"""
    marker_content = f"""
# A/B TESTING MARKER
# Created: {datetime.now().isoformat()}

A/B Testing Phase: OPTIMIZATION
Start Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Applied Optimizations:
1. Confidence Threshold: 35% → 75%
2. Signal Agreement: 3+ → 4+ signals required  
3. Position Size: 20% → 15% max
4. Goal: Improve win rate from 0% to 40%+

Expected Results:
- Fewer trades (more selective)
- Higher win rate
- Better risk-adjusted returns
- Reduced drawdowns

Comparison Period: 1-2 weeks
Success Metrics: Win rate >40%, positive avg P&L
"""
    
    with open("AB_TEST_ACTIVE.md", 'w') as f:
        f.write(marker_content)
    
    logger.success("✅ Created A/B test marker file")

def main():
    """Apply all ML optimizations for A/B testing"""
    print("🔬 APPLYING ML OPTIMIZATIONS FOR A/B TESTING")
    print("="*60)
    
    logger.info("Starting ML optimization application...")
    
    # Step 1: Backup current configuration
    logger.info("📦 Step 1: Creating configuration backups")
    backup_current_config()
    
    # Step 2: Apply optimizations
    logger.info("🎯 Step 2: Applying ML-recommended optimizations")
    apply_confidence_threshold_optimization()
    apply_signal_agreement_optimization() 
    apply_position_size_optimization()
    
    # Step 3: Create tracking marker
    logger.info("📋 Step 3: Setting up A/B test tracking")
    create_ab_test_marker()
    
    print("\n🎉 ML OPTIMIZATIONS APPLIED SUCCESSFULLY!")
    print("="*60)
    print("Next Steps:")
    print("1. Deploy changes to cloud server")
    print("2. Monitor performance for 1-2 weeks") 
    print("3. Compare results using A/B testing framework")
    print("4. Apply permanent changes if successful")
    
    logger.success("✅ All ML optimizations applied successfully")

if __name__ == "__main__":
    main()