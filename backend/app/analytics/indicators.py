from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from backend.app.core.exceptions import CalculationException
from backend.app.schemas.market_data import PriceBarRead


class TechnicalAnalytics:
    """Deterministic quantitative calculations for equity price bars."""

    @staticmethod
    def calculate_price_changes(current_price: float, previous_price: float) -> Dict[str, float]:
        """Calculate absolute and percentage price change with zero-denominator safety."""
        if previous_price is None or np.isnan(previous_price):
            raise CalculationException("Previous price is undefined or NaN.")
        if previous_price == 0:
            raise CalculationException("Previous price is zero; cannot compute percentage change.")

        absolute_change = round(current_price - previous_price, 4)
        pct_change = round((absolute_change / abs(previous_price)) * 100.0, 4)
        return {
            "absolute_change": absolute_change,
            "percentage_change": pct_change,
        }

    @staticmethod
    def calculate_simple_moving_average(prices: List[float], period: int = 20) -> List[Optional[float]]:
        """Calculate Simple Moving Average (SMA)."""
        if period <= 0:
            raise CalculationException(f"Period must be greater than 0, got {period}")
        if len(prices) < period:
            return [None] * len(prices)

        series = pd.Series(prices)
        sma = series.rolling(window=period).mean()
        return [round(val, 2) if pd.notna(val) else None for val in sma]

    @staticmethod
    def calculate_exponential_moving_average(prices: List[float], period: int = 20) -> List[Optional[float]]:
        """Calculate Exponential Moving Average (EMA)."""
        if period <= 0:
            raise CalculationException(f"Period must be greater than 0, got {period}")
        if len(prices) < period:
            return [None] * len(prices)

        series = pd.Series(prices)
        ema = series.ewm(span=period, adjust=False).mean()
        return [round(val, 2) if pd.notna(val) else None for val in ema]

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index (RSI) with 0-100 bounds and division-by-zero protection."""
        if period <= 0:
            raise CalculationException(f"Period must be greater than 0, got {period}")
        if len(prices) <= period:
            return [None] * len(prices)

        series = pd.Series(prices)
        delta = series.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rsi_list: List[Optional[float]] = []
        for g, l in zip(avg_gain, avg_loss):
            if pd.isna(g) or pd.isna(l):
                rsi_list.append(None)
            elif l == 0:
                rsi_list.append(100.0)
            elif g == 0:
                rsi_list.append(0.0)
            else:
                rs = g / l
                rsi = 100.0 - (100.0 / (1.0 + rs))
                rsi_list.append(round(float(rsi), 2))

        return rsi_list

    @staticmethod
    def calculate_historical_volatility(prices: List[float], trading_days: int = 252) -> Optional[float]:
        """Annualized historical volatility based on log returns."""
        if len(prices) < 2:
            return None

        arr = np.array(prices, dtype=float)
        # Avoid zero or negative values in log
        valid_mask = arr > 0
        arr = arr[valid_mask]
        if len(arr) < 2:
            return None

        log_returns = np.diff(np.log(arr))
        if len(log_returns) == 0:
            return None

        daily_std = np.std(log_returns, ddof=1)
        annualized_vol = daily_std * np.sqrt(trading_days)
        return round(float(annualized_vol) * 100.0, 2)

    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> Dict[str, float]:
        """Calculate maximum peak-to-trough drawdown."""
        if not prices or len(prices) < 2:
            return {"max_drawdown_pct": 0.0, "peak_price": 0.0, "trough_price": 0.0}

        series = pd.Series(prices)
        running_max = series.cummax()
        drawdown = (series - running_max) / running_max
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()

        peak = running_max.loc[max_dd_idx]
        trough = series.loc[max_dd_idx]

        return {
            "max_drawdown_pct": round(float(max_dd) * 100.0, 2),
            "peak_price": round(float(peak), 2),
            "trough_price": round(float(trough), 2),
        }

