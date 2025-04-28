import numpy as np
from numba import njit

@njit
def calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    alpha = 2 / (period + 1)
    ema = np.empty_like(data)
    ema[0] = data[0]  # seed with first price
    
    for i in range(1, data.shape[0]):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
    
    return ema

@njit
def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int=14) -> np.ndarray:
    atr = np.empty_like(close)
    tr = np.empty_like(close)
    
    tr[0] = high[0] - low[0]
    for i in range(1, close.shape[0]):
        h_l = high[i] - low[i]
        h_pc = abs(high[i] - close[i - 1])
        l_pc = abs(low[i] - close[i - 1])
        tr[i] = max(h_l, h_pc, l_pc)

    # First ATR point is SMA of first `period` TRs
    atr[:period] = np.nan
    atr[period - 1] = np.mean(tr[:period])
    
    # Rest: EMA-style smoothing
    alpha = 1 / period
    for i in range(period, close.shape[0]):
        atr[i] = alpha * tr[i] + (1 - alpha) * atr[i - 1]
    
    return atr

@njit
def calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
    n = data.shape[0]
    sma = np.empty(n)
    sma[:period-1] = np.nan

    window_sum = 0.0
    for i in range(period):
        window_sum += data[i]
    sma[period - 1] = window_sum / period

    for i in range(period, n):
        window_sum += data[i] - data[i - period]
        sma[i] = window_sum / period

    return sma

@njit
def calculate_ema_slope_simple(ema_values: np.ndarray, lookback: int = 10) -> np.ndarray:
    n = len(ema_values)
    slopes = np.empty(n)
    
    for i in range(lookback):
        slopes[i] = np.nan  # Fill front NaNs
    
    for i in range(lookback, n):
        slopes[i] = (ema_values[i] - ema_values[i - lookback]) / lookback

    return slopes

@njit
def calculate_ema_slope_linreg(ema_values: np.ndarray, lookback: int = 10) -> np.ndarray:
    n = len(ema_values)
    slopes = np.empty(n)
    x = np.arange(lookback)
    x_mean = np.mean(x)
    x_demean = x - x_mean
    denom = np.sum(x_demean ** 2)

    for i in range(lookback):
        slopes[i] = np.nan

    for i in range(lookback, n):
        window = ema_values[i - lookback:i]
        y_mean = np.mean(window)
        y_demean = window - y_mean
        slope = np.sum(x_demean * y_demean) / denom
        slopes[i] = slope

    return slopes

@njit
def calculate_ema_slope(ema_values: np.ndarray, lookback: int=10, method: str='simple') -> np.ndarray:
    match method:
        case 'simple':
            return calculate_ema_slope_simple(ema_values, lookback)
        case 'linreg':
            return calculate_ema_slope_linreg(ema_values, lookback)
        case _:
            raise ValueError("Invalid method. Use 'simple' or 'linreg'.")

@njit
def daily_rolling_median_atr(atr: np.ndarray, candles_per_day: int = 75, window_days: int = 30) -> np.ndarray:
    n_candles = len(atr)
    n_days = n_candles // candles_per_day
    median_atr_per_day = np.full(n_days, np.nan)

    for i in range(window_days, n_days):
        start_idx = (i - window_days) * candles_per_day
        end_idx = i * candles_per_day
        window = atr[start_idx:end_idx]
        median_atr_per_day[i] = np.nanmedian(window)

    # Broadcast per-day median ATR back to per-candle resolution
    full_median_array = np.empty(n_candles)
    for i in range(n_days):
        day_start = i * candles_per_day
        day_end = day_start + candles_per_day
        val = median_atr_per_day[i] if i < len(median_atr_per_day) else np.nan
        for j in range(day_start, min(day_end, n_candles)):
            full_median_array[j] = val

    return full_median_array

