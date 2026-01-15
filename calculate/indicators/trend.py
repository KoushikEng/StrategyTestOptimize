"""
Trend Indicators
"""

import numpy as np
from numba import njit
from .core import *
from collections import namedtuple

ADXResult = namedtuple('ADXResult', ['adx', 'pdi', 'mdi'])

@njit
def calculate_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14):
    # SIGNATURE: args=["highs", "lows", "closes"] defaults={"period": 14}
    """
    Calculate ADX. Returns NamedTuple(adx, pdi, mdi).
    """
    n = len(close)
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    tr = np.zeros(n)

    for i in range(1, n):
        up_move = high[i] - high[i - 1]
        down_move = low[i - 1] - low[i]

        plus_dm[i] = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm[i] = down_move if (down_move > up_move and down_move > 0) else 0.0

        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1])
        )

    # Wilder's smoothing (EMA approximation)
    atr = np.zeros(n)
    plus_di = np.zeros(n)
    minus_di = np.zeros(n)
    dx = np.zeros(n)
    adx = np.zeros(n)

    # Initial ATR
    atr[period] = np.mean(tr[1:period+1])
    plus_dm_sum = np.sum(plus_dm[1:period+1])
    minus_dm_sum = np.sum(minus_dm[1:period+1])

    plus_di[period] = 100 * (plus_dm_sum / atr[period])
    minus_di[period] = 100 * (minus_dm_sum / atr[period])
    dx[period] = 100 * abs(plus_di[period] - minus_di[period]) / (plus_di[period] + minus_di[period])

    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        plus_dm[i] = (plus_dm[i - 1] * (period - 1) + plus_dm[i]) / period
        minus_dm[i] = (minus_dm[i - 1] * (period - 1) + minus_dm[i]) / period

        plus_di[i] = 100 * (plus_dm[i] / atr[i])
        minus_di[i] = 100 * (minus_dm[i] / atr[i])
        dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i])

    adx[period * 2] = np.mean(dx[period:period * 2])
    for i in range(period * 2 + 1, n):
        adx[i] = ((adx[i - 1] * (period - 1)) + dx[i]) / period

    return ADXResult(adx, plus_di, minus_di)

@njit
def calculate_supertrend(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int=10, multiplier: float=3.0) -> np.ndarray:
    # SIGNATURE: args=["highs", "lows", "closes"] defaults={"period": 10, "multiplier": 3.0}
    """
    Calculate Supertrend.
    """
    n = len(close)
    
    # --- ATR Calculation ---
    atr = calculate_atr(high, low, close, period)

    # --- Supertrend Calculation ---
    upperband = np.empty(n)
    lowerband = np.empty(n)
    trend = np.ones(n, dtype=np.int8)  # Default to uptrend

    for i in range(n):
        upperband[i] = ((high[i] + low[i]) / 2) + multiplier * atr[i]
        lowerband[i] = ((high[i] + low[i]) / 2) - multiplier * atr[i]

    final_upperband = upperband.copy()
    final_lowerband = lowerband.copy()

    for i in range(period, n):
        # Carry forward bands
        if close[i - 1] > final_upperband[i - 1]:
            trend[i] = 1
        elif close[i - 1] < final_lowerband[i - 1]:
            trend[i] = -1
        else:
            trend[i] = trend[i - 1]
            if trend[i] == 1 and lowerband[i] < final_lowerband[i - 1]:
                final_lowerband[i] = lowerband[i]
            else:
                final_lowerband[i] = final_lowerband[i - 1]
            if trend[i] == -1 and upperband[i] > final_upperband[i - 1]:
                final_upperband[i] = upperband[i]
            else:
                final_upperband[i] = final_upperband[i - 1]

    return trend

# Namedtuple for the result
IchimokuResult = namedtuple(
    'IchimokuResult',
    ['tenkan', 'kijun', 'senkou_a', 'senkou_b', 'chikou']
)

@njit
def calculate_ichimoku(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> IchimokuResult:
    # SIGNATURE: args=["highs", "lows", "closes"] defaults={}
    """
    Calculate the Ichimoku Kinko Hyo indicator components.

    Parameters
    ----------
    high : np.ndarray
        Array of high prices.
    low : np.ndarray
        Array of low prices.
    close : np.ndarray
        Array of close prices.

    Returns
    -------
    IchimokuResult
        Namedtuple containing the following arrays:
        - tenkan: Tenkan-sen (conversion line)
        - kijun: Kijun-sen (base line)
        - senkou_a: Senkou Span A (leading span A)
        - senkou_b: Senkou Span B (leading span B)
        - chikou: Chikou Span (lagging line)
    """
    n = high.shape[0]
    # Initialize output arrays with NaNs
    tenkan = np.full(n, np.nan, dtype=np.float64)
    kijun = np.full(n, np.nan, dtype=np.float64)
    senkou_a = np.full(n, np.nan, dtype=np.float64)
    senkou_b = np.full(n, np.nan, dtype=np.float64)
    chikou = np.full(n, np.nan, dtype=np.float64)

    # Tenkan-sen (9-period)
    for i in range(8, n):
        high_window = high[i-8:i+1]
        low_window = low[i-8:i+1]
        tenkan[i] = (np.max(high_window) + np.min(low_window)) / 2.0

    # Kijun-sen (26-period)
    for i in range(25, n):
        high_window = high[i-25:i+1]
        low_window = low[i-25:i+1]
        kijun[i] = (np.max(high_window) + np.min(low_window)) / 2.0

    # Senkou Span A (average of Tenkan and Kijun, plotted 26 periods ahead)
    for i in range(8, n):
        if not np.isnan(tenkan[i]) and not np.isnan(kijun[i]):
            idx = i + 26
            if idx < n:
                senkou_a[idx] = (tenkan[i] + kijun[i]) / 2.0

    # Senkou Span B (52-period, plotted 26 periods ahead)
    for i in range(51, n):
        high_window = high[i-51:i+1]
        low_window = low[i-51:i+1]
        value = (np.max(high_window) + np.min(low_window)) / 2.0
        idx = i + 26
        if idx < n:
            senkou_b[idx] = value

    # Chikou Span (close plotted 26 periods behind)
    for i in range(26, n):
        chikou[i] = close[i-26]

    return IchimokuResult(tenkan, kijun, senkou_a, senkou_b, chikou)
