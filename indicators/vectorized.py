import numpy as np

def vectorized_atr(high, low, close, period=14):
    tr = np.maximum.reduce([
        high - low,
        np.abs(high - np.roll(close, 1)),
        np.abs(low - np.roll(close, 1))
    ])
    tr[0] = np.nan  # First TR is NaN
    
    # Calculate ATR using EMA (approximates Wilder's smoothing)
    atr = np.zeros_like(tr)
    atr[period - 1] = np.nanmean(tr[:period])
    alpha = 1 / period  # EMA smoothing factor
    
    # Vectorized EMA calculation
    atr[period:] = (1 - alpha) * atr[period - 1:-1] + alpha * tr[period:]
    return atr