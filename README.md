# 🚀 RTX AlgoSlayer - Multi-AI Options Trading Bot

**Autonomous RTX options trading with multi-AI signal fusion for high-probability trades.**

## 🎯 Strategy Overview

- **Target**: RTX (Raytheon Technologies) options trading
- **Capital**: Starting with ~$1,000 (9 RTX shares)
- **Goal**: 80-90% win rate with small, consistent profits
- **Approach**: Multi-AI signal fusion for high-confidence trades only

## 🧠 AI Signal Sources

### Currently Implemented:
- **News Sentiment**: OpenAI analysis of RTX & defense sector news
- **Signal Fusion Engine**: Combines multiple AI signals with weighted confidence

### Planned Signals:
- **Options Flow**: Unusual activity detection and smart money following
- **Technical Analysis**: Mean reversion, volatility patterns, sector correlation
- **Event Prediction**: Geopolitical events, defense spending, earnings sentiment
- **Volatility Analysis**: IV crush opportunities and volatility trading

## 🏗️ Architecture

```
RTX AlgoSlayer/
├── src/
│   ├── signals/           # Modular AI signal modules
│   │   ├── base_signal.py         # Base signal interface
│   │   ├── news_sentiment_signal.py   # OpenAI news analysis
│   │   └── [future signals...]
│   ├── core/              # Core trading engine
│   │   ├── signal_fusion.py       # Multi-AI signal combiner
│   │   └── [execution engine...]
│   └── brokers/           # Broker integrations
│       └── [interactive_brokers.py...]
├── config/
│   └── trading_config.py  # All configuration in one place
├── logs/                  # Trading logs and decisions
└── tests/                 # Backtesting and strategy tests
```

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
# Copy and edit environment file
cp env_template.txt .env
# Add your OpenAI API key and other credentials
```

### 3. Test the AI Signals
```bash
python test_signals.py
```

### 4. Configuration
Edit `config/trading_config.py` to adjust:
- Signal weights and thresholds
- Risk management parameters
- Position sizing rules
- Paper vs live trading

## 🎛️ Configuration

### Signal Weights (easily adjustable):
```python
SIGNAL_WEIGHTS = {
    "news_sentiment": 0.3,      # OpenAI news analysis
    "options_flow": 0.25,       # Smart money following
    "technical_analysis": 0.2,   # Chart patterns
    "volatility_analysis": 0.15, # IV opportunities
    "sector_correlation": 0.1    # Defense sector trends
}
```

### Risk Management:
- **Max Position Size**: $200 per trade
- **Stop Loss**: 25% of position
- **Daily Loss Limit**: $50
- **Minimum Confidence**: 75% before trading

## 🔄 Trading Logic

1. **Signal Collection**: Gather AI signals in parallel
2. **Fusion Analysis**: Combine signals with weighted confidence
3. **Decision Making**: Trade only when multiple signals agree
4. **Position Sizing**: Scale based on confidence and risk
5. **Execution**: Paper trade first, then live trading

## 📊 Backtesting

Each signal module includes backtesting capabilities:
```python
# Test individual signals
await signal.backtest("RTX", "2024-01-01", "2024-12-01")

# Test full fusion strategy
await fusion_engine.backtest_strategy("RTX", "2024-01-01", "2024-12-01")
```

## 🛡️ Risk Management

- **Capital Preservation**: Only 15% of capital per trade
- **High Confidence Required**: 75%+ confidence threshold
- **Multiple Signal Confirmation**: Minimum 3 signals must agree
- **Commission Aware**: All strategies factor in $0.65/contract IB fees

## 🚧 Development Roadmap

### Phase 1: ✅ Foundation
- [x] Modular signal architecture
- [x] OpenAI news sentiment analysis
- [x] Signal fusion engine
- [x] Configuration system

### Phase 2: 🚧 Core Signals
- [ ] Options flow analysis
- [ ] Technical analysis signals
- [ ] Volatility analysis
- [ ] Sector correlation

### Phase 3: 📈 Execution
- [ ] Interactive Brokers integration
- [ ] Paper trading implementation
- [ ] Live trading execution
- [ ] Performance monitoring

### Phase 4: 🧠 Advanced AI
- [ ] Machine learning signal optimization
- [ ] Dynamic weight adjustment
- [ ] Market regime detection
- [ ] Adaptive strategy selection

## 💡 Usage Examples

### Basic Signal Testing:
```python
from src.core.signal_fusion import SignalFusionEngine

# Initialize and test
fusion_engine = SignalFusionEngine()
decision = await fusion_engine.make_trading_decision("RTX")
print(f"Action: {decision.action}, Confidence: {decision.confidence:.2%}")
```

### Adding New Signals:
```python
from src.signals.base_signal import BaseSignal

class MyCustomSignal(BaseSignal):
    async def analyze(self, symbol: str) -> SignalResult:
        # Your signal logic here
        return SignalResult(...)

# Add to fusion engine
fusion_engine.add_signal(MyCustomSignal())
```

## ⚠️ Important Notes

- **Start with Paper Trading**: Always test strategies before using real money
- **Small Capital Strategy**: Designed for ~$1,000 starting capital
- **Commission Sensitive**: All profits must exceed $0.65+ per contract
- **RTX Focused**: Initially optimized for RTX options specifically

## 📈 Expected Performance

- **Win Rate Target**: 80-90%
- **Average Trade**: $20-50 profit
- **Trade Frequency**: 2-5 trades per week
- **Monthly Target**: 8-15% return on capital

## 🔧 Troubleshooting

### Common Issues:
1. **OpenAI API Errors**: Check your API key in `.env`
2. **Import Errors**: Ensure all dependencies are installed
3. **Configuration Issues**: Verify `config/trading_config.py` settings

### Logs:
Check `logs/rtx_trading.log` for detailed execution logs and debugging info.

---

**⚡ Built for speed, designed for profit, powered by AI.**

*Ready to make your RTX shares work harder!* 🚀