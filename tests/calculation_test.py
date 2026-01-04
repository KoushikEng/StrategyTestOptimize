import numpy as np
from numba import njit, float64, int64

# Assume high, low, and close are NumPy arrays of the same length
# For example:
high_prices = np.random.randint(50, 151, size=100) + np.random.rand(100)
low_prices = np.random.randint(50, 151, size=100) + np.random.rand(100)
close_prices = np.random.randint(50, 151, size=100) + np.random.rand(100)

@njit
def numba_atr(high, low, close, period=14):
    n = len(close)
    tr = np.empty(n)
    tr[0] = np.nan

    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1])
        )

    atr = np.zeros_like(tr)

    atr[period - 1] = np.nanmean(tr[:period])  # SMA seed

    alpha = 1.0 / period
    
    atr[period] = (1 - alpha) * atr[period - 1]
    
    for i in range(period, n):
        atr[i] += alpha * tr[i]

    return atr


numba_atr_values = numba_atr(high_prices, low_prices, close_prices)
print("Numba ATR:", numba_atr_values)

# Verify against the original vectorized function (for comparison)
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

vectorized_atr_values = vectorized_atr(high_prices, low_prices, close_prices)
print("Vectorized ATR:", vectorized_atr_values)

print("Are the results close?", np.allclose(numba_atr_values, vectorized_atr_values, equal_nan=True))