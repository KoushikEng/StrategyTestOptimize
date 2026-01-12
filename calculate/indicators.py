"""
This module provides a collection of technical indicators implemented using Numba for efficient computation.
"""

import numpy as np
from numba import njit


@njit
def calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate the Simple Moving Average (SMA) for a given array of data.
    
    Args:
        data (np.ndarray): Array of data points.
        period (int): Period for SMA calculation.
    
    Returns:
        np.ndarray: Array of SMA values.
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
    Calculate the Exponential Moving Average (EMA) for a given array of data.
    
    Args:
        data (np.ndarray): Array of data points.
        period (int): Period for EMA calculation.
    
    Returns:
        np.ndarray: Array of EMA values.
    """
    alpha = 2 / (period + 1)
    ema = np.zeros_like(data)
    ema[0] = data[0]  # seed with first price
    
    for i in range(1, data.shape[0]):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
    
    return ema

@njit
def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Calculate the MACD (Moving Average Convergence Divergence) for a given array of prices.
    
    Args:
        prices (np.ndarray): Array of prices.
        fast (int): Fast EMA period (default is 12).
        slow (int): Slow EMA period (default is 26).
        signal (int): Signal EMA period (default is 9).
    
    Returns:
        tuple: Tuple containing MACD line, Signal line, and Histogram.
    """
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line

@njit
def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int=14) -> np.ndarray:
    """
    Calculate the Average True Range (ATR) for a given array of prices.
    
    Args:
        high (np.ndarray): Array of high prices.
        low (np.ndarray): Array of low prices.
        close (np.ndarray): Array of close prices.
        period (int): Period for ATR calculation (default is 14).
    
    Returns:
        np.ndarray: Array of ATR values.
    """
    atr = np.zeros_like(close)
    tr = np.empty_like(close)
    
    tr[0] = high[0] - low[0]
    for i in range(1, close.shape[0]):
        h_l = high[i] - low[i]
        h_pc = abs(high[i] - close[i - 1])
        l_pc = abs(low[i] - close[i - 1])
        tr[i] = max(h_l, h_pc, l_pc)

    # First ATR point is SMA of first `period` TRs
    atr[period - 1] = np.mean(tr[:period])
    
    # Rest: EMA-style smoothing
    alpha = 1 / period
    for i in range(period, close.shape[0]):
        atr[i] = alpha * tr[i] + (1 - alpha) * atr[i - 1]
    
    return atr

@njit
def calculate_supertrend(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int=10, multiplier: float=3.0) -> np.ndarray:
    """
    Calculate the Supertrend for a given array of prices.
    
    Args:
        high (np.ndarray): Array of high prices.
        low (np.ndarray): Array of low prices.
        close (np.ndarray): Array of close prices.
        period (int): Period for Supertrend calculation (default is 10).
        multiplier (float): Multiplier for ATR (default is 3.0).
    
    Returns:
        np.ndarray: Array of Supertrend values.
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

    return trend  # 1 for uptrend, -1 for downtrend

@njit
def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate the Relative Strength Index (RSI) for a given array of prices.
    
    Args:
        prices (np.ndarray): Array of prices.
        period (int): Period for RSI calculation (default is 14).
    
    Returns:
        np.ndarray: Array of RSI values.
    """
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = np.maximum(-deltas, 0)
    
    # EMA of gains/losses
    avg_gain = np.full_like(prices, np.nan)
    avg_loss = np.full_like(prices, np.nan)
    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])
    
    for i in range(period + 1, len(prices)):
        avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
        avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period
    
    rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
    return 100 - (100 / (1 + rs))

@njit
def calculate_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate the Average Directional Index (ADX) for a given array of prices.
    
    Args:
        high (np.ndarray): Array of high prices.
        low (np.ndarray): Array of low prices.
        close (np.ndarray): Array of close prices.
        period (int): Period for ADX calculation (default is 14).
    
    Returns:
        tuple: Tuple containing ADX values, plus DI, and minus DI.
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

    return adx, plus_di, minus_di  # ADX values: higher = stronger trend

@njit
def calculate_vwap(high, low, close, volume):
    """
    Calculate the Volume Weighted Average Price (VWAP) for a given array of prices.
    
    Args:
        high (np.ndarray): Array of high prices.
        low (np.ndarray): Array of low prices.
        close (np.ndarray): Array of closing prices.
        volume (np.ndarray): Array of volumes.
    
    Returns:
        np.ndarray: Array of VWAP values.
    """
    n = len(close)
    vwap = np.empty(n)
    cumulative_vp = 0.0
    cumulative_volume = 0.0

    for i in range(n):
        typical_price = (high[i] + low[i] + close[i]) / 3
        cumulative_vp += typical_price * volume[i]
        cumulative_volume += volume[i]
        vwap[i] = cumulative_vp / cumulative_volume if cumulative_volume != 0 else 0.0

    return vwap

@njit
def _calculate_rolling_std(data: np.ndarray, window: int) -> np.ndarray:
    result = np.full(len(data), np.nan, dtype=float)
    for i in range(window-1, len(data)):
        window_data = data[i-window+1:i+1]
        result[i] = np.std(window_data)
    return result

@njit
def calculate_bollinger_bands(data: np.ndarray, window: int, num_std: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate the Bollinger Bands for a given array of prices.
    
    Args:
        data (np.ndarray): Array of prices.
        window (int): Number of periods to consider for Bollinger Bands calculation (default is 20).
        num_std (float): Number of standard deviations to use for Bollinger Bands calculation (default is 2.0).
    
    Returns:
        tuple: Tuple containing middle band, upper band, and lower band as numpy arrays.
    """
    middle_band = calculate_sma(data, window)
    std_dev = _calculate_rolling_std(data, window)
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    
    return middle_band, upper_band, lower_band
