#!/usr/bin/env python3
"""Unit tests for the options data engine."""

from types import SimpleNamespace

import pandas as pd
import pytest

from config.options_config import options_config
from src.core.options_data_engine import OptionsDataEngine


class DummyTicker:
    """Minimal ticker stub returning deterministic option data."""

    def __init__(self, calls: pd.DataFrame, puts: pd.DataFrame):
        self.options = ["2099-01-05"]
        self._chain = SimpleNamespace(calls=calls, puts=puts)

    def option_chain(self, exp_date: str) -> SimpleNamespace:  # pragma: no cover - simple passthrough
        return self._chain


@pytest.fixture()
def sample_ticker():
    call_rows = pd.DataFrame(
        [
            {
                "contractSymbol": "RTXDUMMYC",
                "strike": 121.0,
                "bid": 2.5,
                "ask": 2.7,
                "lastPrice": 2.6,
                "volume": 250,
                "openInterest": 320,
                "impliedVolatility": 0.25,
                "delta": 0.55,
                "gamma": 0.04,
                "theta": -0.02,
                "vega": 0.11,
            },
            {
                "contractSymbol": "RTXDUMMYC2",
                "strike": 122.0,
                "bid": 1.9,
                "ask": 2.1,
                "lastPrice": 2.0,
                "volume": 120,
                "openInterest": 210,
                "impliedVolatility": 0.22,
                "delta": 0.48,
                "gamma": 0.03,
                "theta": -0.01,
                "vega": 0.09,
            },
        ]
    )

    put_rows = pd.DataFrame(
        [
            {
                "contractSymbol": "RTXDUMMYP",
                "strike": 119.0,
                "bid": 2.8,
                "ask": 3.1,
                "lastPrice": 3.0,
                "volume": 180,
                "openInterest": 400,
                "impliedVolatility": 0.3,
                "delta": -0.45,
                "gamma": 0.05,
                "theta": -0.015,
                "vega": 0.12,
            }
        ]
    )

    return DummyTicker(call_rows, put_rows)


@pytest.fixture(autouse=True)
def force_market_hours(monkeypatch):
    monkeypatch.setattr(options_config, "is_market_hours", lambda: True)


def test_get_real_options_chain_with_stub(monkeypatch, sample_ticker):
    """Ensure the engine can surface deterministic data without network access."""
    engine = OptionsDataEngine(symbol="RTX", ticker=sample_ticker)
    monkeypatch.setattr(engine, "_is_valid_expiration", lambda _: True)

    chain = engine.get_real_options_chain(force_refresh=True)

    assert len(chain) == 3
    first_contract = next(iter(chain.values()))
    assert first_contract["type"] in {"call", "put"}
    assert first_contract["bid"] < first_contract["ask"]


def test_get_best_options_respects_direction(monkeypatch, sample_ticker):
    """Verify directional filtering returns only relevant contracts."""
    engine = OptionsDataEngine(symbol="RTX", ticker=sample_ticker)
    monkeypatch.setattr(engine, "_is_valid_expiration", lambda _: True)
    monkeypatch.setattr(engine, "get_current_stock_price", lambda: 120.0)

    chain = engine.get_real_options_chain(force_refresh=True)
    engine.cached_chain = chain

    calls = engine.get_best_options_for_direction("BUY", confidence=0.8, account_balance=5000)
    assert calls
    assert all(option["type"] == "call" for option in calls)

    puts = engine.get_best_options_for_direction("SELL", confidence=0.8, account_balance=5000)
    assert puts
    assert all(option["type"] == "put" for option in puts)
