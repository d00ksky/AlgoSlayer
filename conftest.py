"""Pytest configuration for AlgoSlayer."""
from __future__ import annotations

import os
from pathlib import Path

# Integration-style scripts that rely on live data, network services, or
# heavyweight dependencies. We skip them unless the operator opts in.
_INTEGRATION_MODULES = {
    "corrected_signal_test.py",
    "end_to_end_test.py",
    "test_accelerated_learning.py",
    "test_command_integration.py",
    "test_complete_system.py",
    "test_coordination.py",
    "test_cross_strategy_learning.py",
    "test_dashboard.py",
    "test_dashboard_command.py",
    "test_dynamic_thresholds.py",
    "test_exit_conditions.py",
    "test_fixed_fusion.py",
    "test_fixed_system.py",
    "test_fresh_trader.py",
    "test_full_options_trade.py",
    "test_historical_backtest.py",
    "test_ibkr_paper_trading.py",
    "test_kelly_system.py",
    "test_live_trading_simulation.py",
    "test_ml_notifications.py",
    "test_monday_readiness.py",
    "test_multi_strategy_deployment.py",
    "test_new_signals.py",
    "test_notification_formatting_only.py",
    "test_options_prediction.py",
    "test_options_system.py",
    "test_positions.py",
    "test_price_monitoring.py",
    "test_signals.py",
    "test_signals_capture.py",
    "test_system_integration.py",
    "test_telegram_commands.py",
    "test_telegram_formatting.py",
    "test_telegram_notifications.py",
    "test_trade_execution.py",
    "test_trading_system.py",
    "weekend_signal_diagnostics.py",
    "weekend_signal_test.py",
}


def _full_suite_enabled() -> bool:
    value = os.getenv("RUN_FULL_SUITE", "").strip().lower()
    return value in {"1", "true", "yes"}


def pytest_ignore_collect(collection_path, config):  # pragma: no cover - pytest hook
    if _full_suite_enabled():
        return False

    filename = Path(str(collection_path)).name
    return filename in _INTEGRATION_MODULES
