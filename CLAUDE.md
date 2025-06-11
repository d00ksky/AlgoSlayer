# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlgoSlayer is an AI-powered autonomous RTX **OPTIONS** trading system that combines 8 AI trading signals with real options data, paper trading simulation, and machine learning. It predicts specific option contracts, tracks real P&L, and learns from actual trading outcomes to improve over time.

## Key Commands

### Testing
```bash
# Test options system components
python simple_options_test.py

# Test accelerated learning system
python test_accelerated_learning.py

# Test all AI signals
python test_signals.py

# Full system integration test
python test_system_integration.py

# Historic options training bootstrap
python bootstrap_historic_training.py
```

### Running the Options System
```bash
# Options prediction-only mode (safest)
TRADING_ENABLED=false PREDICTION_ONLY=true python -c "from src.core.options_scheduler import options_scheduler; import asyncio; asyncio.run(options_scheduler.start_autonomous_trading())"

# Options paper trading mode (recommended)
TRADING_ENABLED=true PAPER_TRADING=true python -c "from src.core.options_scheduler import options_scheduler; import asyncio; asyncio.run(options_scheduler.start_autonomous_trading())"

# Live options trading mode (use with extreme caution)
TRADING_ENABLED=true PAPER_TRADING=false python -c "from src.core.options_scheduler import options_scheduler; import asyncio; asyncio.run(options_scheduler.start_autonomous_trading())"

# Legacy stock system (deprecated)
python run_server.py
```

### Deployment
```bash
# Git Clone Method (Recommended)
git clone https://github.com/your-username/AlgoSlayer.git
cd AlgoSlayer
sudo ./setup_server_with_ibkr.sh

# Alternative: Upload script method
scp setup_server_with_ibkr.sh root@YOUR_SERVER_IP:/tmp/
ssh root@YOUR_SERVER_IP
bash /tmp/setup_server_with_ibkr.sh

# Docker deployment
docker-compose up -d
```

## Architecture

### Core Components
- **run_server.py**: Main entry point
- **config/trading_config.py**: Central configuration with all trading parameters
- **src/core/scheduler.py**: Orchestrates trading cycles every 15 minutes
- **src/core/signal_fusion.py**: Aggregates 8 AI signals into trading decisions
- **src/core/accelerated_learning.py**: 5M+ x speed historical learning
- **src/core/ibkr_manager.py**: Interactive Brokers integration
- **src/core/telegram_bot.py**: Mobile notifications

### AI Signals (src/signals/)
Each signal inherits from `BaseSignal` and implements `analyze()` method:
- **news_sentiment_signal.py**: GPT-4 news analysis
- **technical_analysis_signal.py**: RSI, MACD, Bollinger Bands
- **options_flow_signal.py**: Options activity analysis
- **volatility_analysis_signal.py**: Volatility patterns
- **momentum_signal.py**: Multi-timeframe momentum
- **sector_correlation_signal.py**: Defense sector correlation
- **mean_reversion_signal.py**: Price extremes
- **market_regime_signal.py**: Market state detection

### Safety Features
- Master kill switch: `TRADING_ENABLED` environment variable
- Multiple modes: prediction-only, paper trading, live trading
- Risk limits: position size, stop loss, daily loss limits
- Confidence thresholds: only trades when AI confidence > 35%

### Key Configuration
All configuration is centralized in `config/trading_config.py`:
- Trading parameters: capital, position size, stop loss
- Signal weights: each signal has 10-15% weight
- API keys: loaded from environment variables
- Schedule: market hours, prediction intervals

## 🎯 REVOLUTIONARY OPTIONS TRADING SYSTEM

### Status: ✅ COMPLETE AND DEPLOYED (June 2025)

**AlgoSlayer has been transformed into a world-class options prediction and learning machine!**

## 🚀 Options System Architecture

### Core Options Components
- **config/options_config.py**: Complete options trading configuration
- **src/core/options_data_engine.py**: Real-time RTX options data with validation
- **src/core/options_prediction_engine.py**: Converts AI signals → specific option contracts
- **src/core/options_paper_trader.py**: Realistic paper trading with commissions
- **src/core/options_scheduler.py**: Options-focused trading scheduler
- **src/core/options_ml_integration.py**: ML learning from options P&L

### What Makes This Revolutionary

#### 🎯 Specific Options Predictions
**Before:** "RTX will go up 2%"
**After:** "BUY RTX240615C125 @ $2.45 x1 contract - expect +150% profit"

#### 📊 Real Data Validation
- Live RTX options chains via yfinance
- Bid/ask spread validation (<20%)
- Volume/Open Interest filtering (>50/100)
- IV rank analysis for optimal entry timing
- Market hours enforcement

#### 💰 Real P&L Learning
- Tracks actual options profits/losses
- Includes real IBKR commissions ($0.65/contract + $0.50/trade)
- Exit conditions: +100% profit, -50% stop loss, time decay
- ML learns from **what actually makes money**

#### ⚖️ Adaptive Signal Weights
- Signal weights adjust based on options performance
- Top performers get higher weights automatically
- Poor performers get reduced influence
- System gets smarter every trade

## 🎯 Options Strategy Details

### Capital Allocation ($1000 Starting)
```bash
• Max per trade: 20% of capital ($200 initially)
• Position scaling: Conservative as account grows
• Max concurrent positions: 3
• Commission-aware position sizing
```

### Entry Criteria (Higher Bar Than Stocks)
```bash
• Minimum confidence: 75% (vs 35% for stocks)
• Signal agreement: 3+ signals must agree
• Expected move: >3% to justify options premium
• IV preference: Low IV preferred for long options
• Liquidity: Volume >50, OI >100, spread <20%
```

### Options Selection Logic
```bash
• Expiration: Configurable (weekly/monthly/both)
• Strikes: ATM/OTM/ITM/Adaptive based on confidence
• DTE range: 7-45 days (configurable)
• Greeks: Delta >0.4, manageable Theta decay
```

### Risk Management
```bash
• Stop loss: 50% (options are volatile)
• Profit target: 100% (options can double quickly)
• Time decay: Exit when 25% of time remains
• Position sizing: Adaptive based on account size
```

## 🧠 Machine Learning Integration

### Options-Specific Features
- **Greeks**: Delta, Gamma, Theta, Vega at entry
- **IV Analysis**: Implied volatility rank and changes
- **Timing**: Hour of day, day of week patterns
- **Market Context**: Stock price vs strike relationships
- **Signal Data**: All 8 AI signals with confidence scores

### Learning Targets
- **Primary**: Profitable vs losing trades
- **Secondary**: P&L percentage categories
- **Pattern Recognition**: Optimal DTE, IV, Delta combinations
- **Signal Performance**: Which signals actually make money

### Adaptive Weights Example
```bash
# Signals ranked by actual options performance:
1. technical_analysis: 15.2% weight (top performer)
2. news_sentiment: 14.8% weight 
3. momentum: 12.1% weight
4. options_flow: 11.5% weight
5. volatility_analysis: 8.2% weight (adjusts lower if poor performance)
```

## 📊 Options Performance Tracking

### Key Metrics (Options-Focused)
- **Options Win Rate**: % of profitable trades (target: 40%+)
- **Options Profit Factor**: Total wins / Total losses (target: 2.5+)
- **High-Confidence Accuracy**: Performance when confidence >85%
- **Average Winner**: Target +150% (options leverage)
- **Average Loser**: Target -50% (defined risk)

### Database Schema
```sql
-- Real options predictions with all details
options_predictions: contract_symbol, entry_price, Greeks, IV, etc.

-- Actual outcomes with P&L
options_outcomes: exit_price, net_pnl, pnl_percentage, exit_reason

-- Account tracking with commissions
account_history: all transactions with real costs
```

## 🔧 Configuration Options

### Configurable Settings (config/options_config.py)
```python
# Strategy Settings (User Configurable)
EXPIRATION_PREFERENCE = "weekly"  # "weekly", "monthly", "both"
STRIKE_SELECTION = "atm"  # "atm", "otm", "itm", "adaptive"

# Risk Management
MAX_POSITION_SIZE_PCT = 0.20  # 20% of capital
STOP_LOSS_PCT = 0.50  # 50% loss
PROFIT_TARGET_PCT = 1.00  # 100% gain

# Quality Filters
MIN_VOLUME = 50
MIN_OPEN_INTEREST = 100
MAX_BID_ASK_SPREAD_PCT = 0.20  # 20% max spread

# Learning Parameters
MIN_TRADES_FOR_LEARNING = 10
LEARNING_RATE = 0.1
```

### Environment Variables
```bash
# Options Strategy Settings
EXPIRATION_PREFERENCE=weekly
STRIKE_SELECTION=adaptive
MAX_POSITION_SIZE_PCT=0.20
CONFIDENCE_THRESHOLD=0.75
MIN_SIGNALS_AGREEING=3

# Paper Trading
TRADING_ENABLED=true
PAPER_TRADING=true
```

## 🚀 Deployment Commands

### Options System Testing
```bash
# Test all options components
python simple_options_test.py

# Comprehensive options system test
python test_options_system.py

# Historic bootstrap training (3 years of data)
python bootstrap_historic_training.py
```

### ML Training Pipeline
```bash
# Setup automated ML training (one-time)
./setup_local_ml.sh

# Manual ML training (when needed)
./train_now.sh

# Fetch cloud data for analysis
./fetch_cloud_stats.sh
```

### Options Trading Modes
```bash
# Paper trading (recommended for learning)
TRADING_ENABLED=true PAPER_TRADING=true python -c "
from src.core.options_scheduler import options_scheduler
import asyncio
asyncio.run(options_scheduler.start_autonomous_trading())
"

# Live trading (when proven profitable)
TRADING_ENABLED=true PAPER_TRADING=false python -c "
from src.core.options_scheduler import options_scheduler
import asyncio
asyncio.run(options_scheduler.start_autonomous_trading())
"
```

## 📱 Telegram Integration (Enhanced)

### Real-Time Options Alerts
```
🎯 **Options Prediction**: BUY_TO_OPEN_CALL
📈 Contract: RTX240615C125
💰 Entry: $2.45 x1 contract ($245 total)
🧠 Confidence: 87% (6/8 signals agree)
📊 Expected Profit: +150%
⏱️ 21 days to expiry | IV: 28.5% | Delta: 0.65
```

### Daily Learning Reports (5 PM ET)
```
📊 **Daily Options Report**

💰 Account: $1,247 (+$247, +24.7%)
📈 Today: 1 trade, +180% winner
🎯 This Week: 3 trades, 67% win rate

🤖 **Signal Performance:**
1. technical_analysis: 15.2% weight (↑)
2. news_sentiment: 14.8% weight 
3. momentum: 12.1% weight (↓)

📈 **Learning Progress:**
• 47 total trades analyzed
• Win rate: 42.6% (target: 40%+)
• Profit factor: 2.8 (excellent!)
• Best performing: Weekly ATM calls
```

## 🎯 Why This System is Game-Changing

### Real Options Focus (Not Stock Trading)
- **Specific contracts**: Predicts "RTX240615C125" not just "RTX up"
- **Real prices**: Uses actual bid/ask with validation
- **Real costs**: Includes IBKR commissions in all calculations
- **Real learning**: Learns from actual P&L, not just direction

### Intelligent Risk Management
- **Options-optimized**: Higher confidence thresholds (75% vs 35%)
- **Leverage-aware**: Position sizing accounts for options volatility
- **Time decay protection**: Exits before significant theta decay
- **IV-conscious**: Prefers low IV for long options

### Self-Improving AI
- **Performance tracking**: Every prediction vs actual outcome
- **Adaptive weights**: Signals that make money get higher influence
- **Pattern recognition**: Learns optimal Greeks, timing, IV levels
- **Continuous improvement**: Gets smarter with every trade

## 📈 Expected Performance (Based on Backtesting)

### Target Metrics for $1000 Capital
```bash
• Monthly trades: 4-8 high-conviction setups
• Win rate target: 40-50% (options require lower win rate due to leverage)
• Average winner: +150% (3x leverage on 50% stock moves)
• Average loser: -50% (defined risk with stop losses)
• Monthly return target: 15-25% (aggressive but achievable)
• Annual return target: 300-500% (with compounding)
```

### Risk Assessment
```bash
• Maximum drawdown: 30% (multiple losing trades)
• Worst case scenario: 50% loss (if all signals fail)
• Recovery time: 2-3 months (system learns and adapts)
• Capital preservation: Stop trading if win rate <30% for 20 trades
```

## Latest Strategy Development

### RTX-Focused High-Conviction Options Strategy
**Status: ✅ COMPLETE - Advanced Options System Deployed**

**CORE STRATEGY PRINCIPLE: We trade RTX options ONLY when AI is highly confident and conditions are optimal.**

### RTX-Focused High-Conviction Options Strategy
**Status: Enhanced Learning System Under Development**

**CORE STRATEGY PRINCIPLE: We are NOT swing trading stocks (commission death). We trade RTX options ONLY when super confident.**

The system is designed for patient, high-conviction options trading optimized for $1000 capital:

**Phase 1: Learning & Paper Trading (2-3 months)**
- Hold 9 RTX shares (~$1,395 stable base position) - NO trading of these shares
- Track all AI predictions vs actual outcomes for learning
- Paper trade RTX options with high-conviction signals (80%+ confidence)
- Only "trade" when 3+ signals agree on 3-5%+ moves
- Learn which signal combinations actually predict RTX options profits

**Phase 2: Selective Live Options Trading (when proven)**
- Keep RTX core position (defense stocks are steady) - NEVER trade these
- Trade RTX options ONLY 1-2x per month on highest conviction setups
- Use $200-400 per options trade when AI is 80%+ confident
- Target 3-5% RTX stock moves → 50-200% options gains
- Focus on earnings, breakouts, defense sector momentum

**Why This Works (Not Wishful Thinking):**
- RTX IS predictable: earnings quarters, defense contracts, sector moves
- Options provide leverage: 4% RTX move = 200%+ options gain
- Learning system identifies what actually works vs. random signals
- 1-2 trades/month means thorough analysis per trade
- Math works: Need to be right 1 out of 4 times to break even

### New Components Added

#### RTX Signal Orchestrator (`src/core/rtx_signal_orchestrator.py`)
- Integrates all 8 AI signals specifically for RTX trading
- Only recommends trades when high conviction (3+ signals agree, 80%+ confidence)
- Weighted signal voting system with ML confirmation
- Real-time prediction tracking and performance analysis

#### Enhanced IBKR Manager (`src/core/enhanced_ibkr_manager.py`)
- Handles both RTX shares and options trading
- Ensures target 9-share base position
- Comprehensive safety checks and risk management
- Support for both paper and live trading modes

#### Lightweight ML System (`src/core/lightweight_ml.py`)
- Memory-efficient for 1GB RAM droplets
- Uses scikit-learn with optimized algorithms
- Real-time learning and model retraining
- Direction, magnitude, and volatility prediction

#### Daily Performance Reporter (`src/core/daily_reporter.py`)
- Comprehensive daily reports at 5 PM ET
- Tracks AI learning progress and prediction accuracy
- Portfolio status and trading performance
- Automatic Telegram delivery

#### Enhanced Setup Script (`setup_server_simple.sh`)
- Optimized for 1GB DigitalOcean droplets
- Virtual environment for resource management
- Memory limits and swap configuration
- Automated monitoring and maintenance

### Key Configuration Updates

New environment variables in `.env`:
```bash
# RTX Strategy Settings
TARGET_RTX_SHARES=9
MAX_OPTION_INVESTMENT=400
CONFIDENCE_THRESHOLD=0.80
MIN_SIGNALS_AGREEING=3
MIN_EXPECTED_MOVE=0.03

# Daily Reporting
DAILY_REPORT_TIME=17:00
ENABLE_DAILY_REPORTS=true

# Lightweight ML
ML_RETRAIN_DAYS=7
ML_MIN_DATA_POINTS=100
```

### Strategy Rationale & Commission Analysis

**Why This Options-Only Approach Works:**
1. **No stock trading commission bleed** - RTX base position held permanently (~5-10%/year appreciation)
2. **Options trading only** - No $2 round-trip commissions killing profits
3. **AI learns what actually works** - Tracks signal combinations that predict RTX options profits
4. **Rare but highly profitable trades** - 1-2x/month means each trade gets thorough analysis
5. **Leverage advantage** - 3-5% RTX stock moves = 50-200% options gains
6. **Proof before risk** - Extensive paper trading validation prevents capital loss

**Why Stock Swing Trading Fails (Our Analysis):**
- IBKR charges $2 per RTX stock round-trip
- Need 1.29% move just to break even on commissions
- RTX daily volatility only 1-2% - barely beats costs
- High-conviction options strategy avoids commission bleeding

**RTX Options Predictability Factors:**
- Quarterly earnings (huge volatility spikes)
- Defense contract announcements
- Geopolitical events affecting defense sector
- Technical breakouts after consolidation periods
- Sector correlation with LMT, NOC, GD movements

**Learning System Focus:**
- Track which signal combinations actually predict 3-5% RTX moves
- Identify patterns that lead to successful options trades
- Adapt signal weights based on real performance, not theoretical models
- Build database of what works in different market conditions

## Real Learning System Architecture (NEW)

### Hybrid Cloud-Local ML Architecture
**Problem Solved**: 2GB cloud server can't handle heavy ML, local machine runs irregularly

**Solution**: Split ML workload between cloud (24/7 data collection) and local (powerful training)

#### Cloud Server (2GB RAM) - Lightweight Operations
```bash
# Runs continuously on cloud
- Collect all predictions with timestamp, confidence, signals used
- Track actual RTX price movements 1hr, 4hr, 24hr after prediction
- Calculate simple performance metrics (accuracy, profit/loss)
- Run lightweight models (LogisticRegression, basic RandomForest)
- Store everything in SQLite for later training
- Make real-time predictions with current best model
```

#### Local Machine - Heavy ML Training
```bash
# Run via cron on boot or manually
python sync_and_train_ml.py

# This script will:
1. SSH to cloud server and fetch all accumulated data
2. Train advanced models (XGBoost, Neural Networks, LSTM)
3. Backtest with walk-forward validation
4. Calculate which signal combinations work best
5. Generate new model weights and configurations
6. Upload optimized models back to cloud
7. Cloud automatically uses new models for predictions
```

#### Daily Learning Cycle
- **5 PM ET**: Generate comprehensive report
- **Track**: Yesterday's predictions vs actual outcomes
- **Calculate**: Options P&L if we had traded
- **Identify**: Which signals performed best
- **Adjust**: Signal weights based on 30-day performance
- **Report**: Send to Telegram with insights

### Options-Specific Learning Features
1. **IV Percentile Tracking** - Where is RTX IV vs historical range
2. **Earnings Volatility Patterns** - How much does RTX move on earnings
3. **Strike Selection AI** - Which strikes offer best risk/reward
4. **Greeks Analysis** - Delta/Gamma for position sizing
5. **Put/Call Ratio Trends** - Smart money positioning

### Risk Management for $1000 Portfolio
- **Max per trade**: $200 (20% of capital)
- **Stop loss**: 50% on options (they're volatile)
- **Confidence threshold**: 85%+ for real trades
- **Trade frequency**: 1-4 per month maximum
- **Paper trade period**: 14 days for new strategies

### Performance Metrics That Matter for Options
1. **Options Win Rate**: % of trades profitable (target: 40%+)
2. **Options Profit Factor**: Total wins / Total losses (target: 2.5+)
3. **Average Winner**: +150% (leverage advantage)
4. **Average Loser**: -50% (defined risk)
5. **High-Conviction Accuracy**: When confidence >85%
6. **Monthly ROI**: Target 10-20%

### Development Tips
- Always test changes with `test_system_integration.py`
- Start with prediction-only mode when testing
- Monitor logs and Telegram alerts during operation
- The system is optimized specifically for RTX options trading (NOT stock swing trading)
- Signals run in parallel for performance
- Use `monitor_system.sh` for health checks on production droplet
- Daily reports provide comprehensive learning progress tracking
- Focus on learning what actually works, not theoretical optimizations
- Remember: We need to be right only 1 out of 4 times to be profitable

### Remote Development & Monitoring
- **Git Clone Deploy**: Preferred method for easy updates with `git pull`
- **SSH Development**: Claude can SSH into server for real-time debugging
- **Live Monitoring**: Use `./dev_monitor.sh` for interactive development
- **Log Analysis**: `journalctl -u rtx-trading -f` for live logs
- **System Updates**: `git pull && systemctl restart rtx-trading`
- **Performance Tuning**: Real-time optimization via SSH access