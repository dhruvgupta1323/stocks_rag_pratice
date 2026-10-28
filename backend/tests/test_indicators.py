import pytest
from backend.app.analytics.indicators import TechnicalAnalytics
from backend.app.core.exceptions import CalculationException


def test_price_changes_valid():
    res = TechnicalAnalytics.calculate_price_changes(current_price=2980.50, previous_price=2960.20)
    assert res["absolute_change"] == 20.30
    assert pytest.approx(res["percentage_change"], 0.01) == 0.686


def test_price_changes_zero_denominator():
    with pytest.raises(CalculationException):
        TechnicalAnalytics.calculate_price_changes(current_price=100.0, previous_price=0.0)


def test_sma_calculation():
    prices = [10.0, 11.0, 12.0, 13.0, 14.0]
    sma = TechnicalAnalytics.calculate_simple_moving_average(prices, period=3)
    assert sma[0] is None
    assert sma[1] is None
    assert sma[2] == 11.0  # (10 + 11 + 12)/3
    assert sma[3] == 12.0  # (11 + 12 + 13)/3
    assert sma[4] == 13.0  # (12 + 13 + 14)/3


def test_rsi_bounds():
    # Monotonically increasing prices should have high RSI
    increasing = [float(i) for i in range(1, 30)]
    rsi = TechnicalAnalytics.calculate_rsi(increasing, period=14)
    valid_rsi = [r for r in rsi if r is not None]
    assert len(valid_rsi) > 0
    assert all(0.0 <= r <= 100.0 for r in valid_rsi)
    assert valid_rsi[-1] == 100.0


def test_drawdown_calculation():
    prices = [100.0, 120.0, 90.0, 110.0]  # Peak 120, trough 90 -> -25%
    dd = TechnicalAnalytics.calculate_max_drawdown(prices)
    assert dd["peak_price"] == 120.0
    assert dd["trough_price"] == 90.0
    assert dd["max_drawdown_pct"] == -25.0


def test_volatility_calculation():
    prices = [100.0, 102.0, 101.0, 103.0, 102.0]
    vol = TechnicalAnalytics.calculate_historical_volatility(prices)
    assert vol is not None
    assert vol > 0.0

