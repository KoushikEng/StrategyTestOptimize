"""
Volatility Indicators
"""

import numpy as np
from numba import njit
from calculate.indicators.core import calculate_sma, _calculate_rolling_std

@njit
def calculate_bollinger_bands(data: np.ndarray, window: int, num_std: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate Bollinger Bands.
    """
    middle_band = calculate_sma(data, window)
    std_dev = _calculate_rolling_std(data, window)
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    
    return middle_band, upper_band, lower_band
