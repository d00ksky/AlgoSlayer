# RTX Trading System - Cloud Data Summary

Generated: Wed Jun 11 16:18:11 CEST 2025
Server: root@64.226.96.90

## System Status
     Active: active (running) since Tue 2025-06-10 17:46:18 UTC; 20h ago
   Main PID: 31086 (python)

## Configuration
```
PAPER_TRADING=true
TRADING_ENABLED=false
PAPER_TRADING=true          # true = fake money, false = real money
PREDICTION_ONLY=false       # true = notifications only, no orders
```

## Recent Predictions Summary
- Total predictions in sample: 12
- High confidence (≥80%): 18

### Latest Predictions
```
2025-06-10 18:01:26 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-10 18:16:29 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-10 18:31:32 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-10 18:46:34 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-10 19:01:37 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-10 19:16:40 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-10 19:46:52 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (75.3%)
2025-06-11 13:35:07 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (68.0%)
2025-06-11 13:50:10 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-11 14:05:13 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (75.3%)
```

### High Confidence Signals
```
2025-06-10 19:01:37 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-10 19:16:40 | INFO     | src.core.scheduler:_execute_trade_decision:249 - 📊 Trade signal: BUY (81.7%) - Trading disabled
2025-06-10 19:16:40 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
2025-06-11 13:50:10 | INFO     | src.core.scheduler:_execute_trade_decision:249 - 📊 Trade signal: BUY (81.7%) - Trading disabled
2025-06-11 13:50:10 | SUCCESS  | src.core.scheduler:_run_prediction_cycle:149 - ✅ Prediction cycle complete: BUY (81.7%)
```

## Errors
```
2025-06-10 19:31:48 | ERROR    | src.core.ibkr_manager:_get_yfinance_data:173 - 📊 yfinance error: argument of type 'NoneType' is not iterable
2025-06-10 19:46:50 | ERROR    | src.signals.options_flow_signal:_get_options_data:79 - 📊 Options data error: Expecting value: line 1 column 1 (char 0)
```
