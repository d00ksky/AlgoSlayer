# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlgoSlayer is an AI-powered autonomous trading system for RTX Corporation stock that combines 8 AI trading signals with Interactive Brokers integration. It features accelerated learning (180x real-time speed), automated trading, and Telegram notifications.

## Key Commands

### Testing
```bash
# Test accelerated learning system
python test_accelerated_learning.py

# Test all AI signals
python test_signals.py

# Full system integration test
python test_system_integration.py
```

### Running the System
```bash
# Prediction-only mode (safest)
TRADING_ENABLED=false PREDICTION_ONLY=true python run_server.py

# Paper trading mode
TRADING_ENABLED=true PAPER_TRADING=true python run_server.py

# Live trading mode (use with extreme caution)
TRADING_ENABLED=true PAPER_TRADING=false python run_server.py
```

### Deployment
```bash
# Deploy to DigitalOcean
./deploy_to_digitalocean.sh

# Docker deployment
docker-compose up -d
```

## Architecture

### Core Components
- **run_server.py**: Main entry point
- **config/trading_config.py**: Central configuration with all trading parameters
- **src/core/scheduler.py**: Orchestrates trading cycles every 15 minutes
- **src/core/signal_fusion.py**: Aggregates 8 AI signals into trading decisions
- **src/core/accelerated_learning.py**: 180x speed historical learning
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

## Latest Strategy Development

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

## Next Development Phase: Enhanced Learning System

### Enhanced Learning Components (✅ COMPLETED)
1. **✅ Signal Performance Tracker** (`src/core/signal_performance_tracker.py`) - Tracks which signals actually predict profitable RTX options trades
2. **✅ RTX Earnings Calendar Integration** (`src/core/rtx_earnings_calendar.py`) - Predictable volatility spikes every quarter
3. **✅ Defense Sector Momentum Analysis** (`src/core/defense_sector_analyzer.py`) - RTX vs ITA ETF correlation
4. **✅ Walk-Forward Backtesting** (`src/core/walk_forward_backtester.py`) - Proper validation to prevent overfitting
5. **✅ Market Regime Detection** (`src/core/market_regime_detector.py`) - Adapt strategy based on bull/bear/sideways markets
6. **✅ Enhanced RTX Signal Orchestrator** - Integrates all learning components with adaptive weights and thresholds

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