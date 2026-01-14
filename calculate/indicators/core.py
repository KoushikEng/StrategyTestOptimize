"""
Core Indicator Primitives
Fundamental calculations used by other indicators.
"""

import numpy as np
from numba import njit

@njit
def calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate the Simple Moving Average (SMA).
    """
    n = data.shape[0]
    sma = np.zeros_like(data)

    window_sum = 0.0
    for i in range(period):
        window_sum += data[i]
    sma[period - 1] = window_sum / period

    for i in range(period, n):
        window_sum += data[i] - data[i - period]
        sma[i] = window_sum / period

    return sma

@njit
def calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate the Exponential Moving Average (EMA).
    """
    alpha = 2 / (period + 1)
    ema = np.zeros_like(data)
    ema[0] = data[0]  # seed with first price
    
    for i in range(1, data.shape[0]):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
    
    return ema

@njit
def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int=14) -> np.ndarray:
    """
    Calculate the Average True Range (ATR).
    """
    n = len(close)
    atr = np.zeros_like(close)
    tr = np.empty_like(close)
    
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        h_l = high[i] - low[i]
        h_pc = abs(high[i] - close[i - 1])
        l_pc = abs(low[i] - close[i - 1])
        tr[i] = max(h_l, h_pc, l_pc)

    # First ATR point is SMA of first `period` TRs
    atr[period - 1] = np.mean(tr[:period])
    
    # Rest: EMA-style smoothing (Wilder's)
    alpha = 1 / period
    for i in range(period, n):
        atr[i] = alpha * tr[i] + (1 - alpha) * atr[i - 1]
    
    return atr

@njit
def _calculate_rolling_std(data: np.ndarray, window: int) -> np.ndarray:
    """
    Calculate Rolling Standard Deviation.
    """
    result = np.full(len(data), np.nan, dtype=np.float64)
    for i in range(window-1, len(data)):
        window_data = data[i-window+1:i+1]
        result[i] = np.std(window_data)
    return result

__all__ = [
    "calculate_sma",
    "calculate_ema",
    "calculate_atr",
    "_calculate_rolling_std"
]
