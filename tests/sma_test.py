import numpy as np
from numba import njit


@njit
def calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
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

def sma_convolve(data, window_size):
    weights = np.ones(window_size) / window_size
    sma = np.convolve(data, weights, mode='valid')
    zero_padding = np.full(window_size - 1, 0)
    return np.concatenate((zero_padding, sma))

if __name__ == "__main__":
    close_prices = np.array([
        29.85, 29.83, 29.90, 30.10, 31.27, 32.00, 31.50, 31.80, 32.10, 32.50,
        32.80, 33.10, 32.90, 33.20, 33.50, 33.80, 33.60, 33.90, 34.20, 34.50,
        34.80, 34.60, 34.90, 35.20, 35.50, 35.80, 35.60, 35.90, 36.20, 36.50
    ])

    sma = calculate_sma(close_prices, 5)
    print(sma)
    sma_conv = sma_convolve(close_prices, 5)
    print(sma_conv)
    print(np.allclose(sma, sma_conv, equal_nan=True))
