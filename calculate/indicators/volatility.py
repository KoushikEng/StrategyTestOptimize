"""
Volatility Indicators
"""

import numpy as np
from numba import njit
from .core import *
from collections import namedtuple

# Define outputs for structured access
BollingerBands = namedtuple('BollingerBands', ['middle', 'upper', 'lower'])

@njit
def calculate_bollinger_bands(data: np.ndarray, window: int, num_std: float = 2.0):
    # SIGNATURE: args=["closes"] defaults={"window": 20, "num_std": 2.0}
    """
    Calculate Bollinger Bands. Returns NamedTuple(middle, upper, lower).
    """
    middle_band = calculate_sma(data, window)
    std_dev = _calculate_rolling_std(data, window)
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    
    return BollingerBands(middle_band, upper_band, lower_band)


KeltnerResult = namedtuple('KeltnerResult', ['middle', 'upper', 'lower'])

@njit
def calculate_keltner_channel(highs, lows, closes, period=20, multiplier=2.0):
    # SIGNATURE: args=["highs", "lows", "closes"] defaults={"period": 20, "multiplier": 2.0}
    """Calculate Keltner Channel.

    Parameters
    ----------
    highs : np.ndarray
        Array of high prices.
    lows : np.ndarray
        Array of low prices.
    closes : np.ndarray
        Array of close prices.
    period : int, optional
        Look‑back period for EMA and ATR. Default is 20.
    multiplier : float, optional
        Multiplier for ATR to determine channel width. Default is 2.0.

    Returns
    -------
    KeltnerResult
        Namedtuple containing the middle, upper, and lower channel arrays.
    """
    middle = calculate_ema(closes, period)
    atr = calculate_atr(highs, lows, closes, period)
    upper = middle + multiplier * atr
    lower = middle - multiplier * atr
    return KeltnerResult(middle, upper, lower)
