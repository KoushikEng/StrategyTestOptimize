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
    """
    Calculate Bollinger Bands. Returns NamedTuple(middle, upper, lower).
    """
    middle_band = calculate_sma(data, window)
    std_dev = _calculate_rolling_std(data, window)
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    
    return BollingerBands(middle_band, upper_band, lower_band)
