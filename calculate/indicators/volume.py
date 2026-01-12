"""
Volume Indicators
"""

import numpy as np
from numba import njit

@njit
def calculate_vwap(high, low, close, volume):
    """
    Calculate Volume Weighted Average Price (VWAP).
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
