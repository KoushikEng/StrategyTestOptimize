"""
Momentum Indicators
"""

import numpy as np
from numba import njit
from calculate.indicators.core import calculate_ema

@njit
def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Calculate the MACD (Moving Average Convergence Divergence).
    """
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line

@njit
def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate the Relative Strength Index (RSI).
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
