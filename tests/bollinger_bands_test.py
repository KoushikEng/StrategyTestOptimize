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


# def rolling_std_numba(a: np.ndarray, n: int) -> np.ndarray:
#     """
#     Calculates the rolling standard deviation of a numpy array.
#     Compatible with Numba's nopython mode.
#     """
#     result = np.full(len(a), np.nan, dtype=float)
#     for i in range(n, len(a)):
#         window = a[i-n:i]
#         result[i] = np.std(window)
#     print(f"result: {result[-5:].tolist()}")
#     return result
    
# def rolling_std(a: np.ndarray, n: int) -> np.ndarray:
#     """
#     Calculates the rolling standard deviation of a numpy array.
#     Compatible with Numba's nopython mode.
#     """
#     result = np.full(len(a), np.nan, dtype=float)
#     for i in range(n - 1, len(a)):
#         window = a[i-n+1:i+1]
#         result[i] = np.std(window)
#     print(f"result: {result[-5:].tolist()}")
#     return result

def rolling_std(data, window_size):
    windows = np.lib.stride_tricks.sliding_window_view(data, window_size)
    
    rolling_std = np.std(windows, axis=-1, ddof=0)
    zero_std = np.zeros(window_size - 1)
    rolling_std = np.concatenate((zero_std, rolling_std))
    print(f"rolling_std: {rolling_std[-5:].tolist()}")

    return rolling_std


def bollinger_bands_numba(data: np.ndarray, window: int, num_std: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculates the Middle, Upper, and Lower Bollinger Bands using numpy
    functions that are compatible with Numba.
    
    Returns a tuple of (middle_band, upper_band, lower_band) as numpy arrays.
    """
    middle_band = calculate_sma(data, window)
    std_dev = rolling_std(data, window)
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    
    return middle_band, upper_band, lower_band

import pandas as pd


def calculate_bollinger_bands(data, window=20, num_std=2):
    """
    Calculates Bollinger Bands using pandas rolling functions.

    Args:
        data (pd.Series or np.array): The price data (e.g., closing prices).
        window (int): The period for the moving average and standard deviation.
        num_std (int): The number of standard deviations for the bands.

    Returns:
        pd.DataFrame: A DataFrame with 'middle_band', 'upper_band', and 'lower_band'.
    """
    # Convert data to pandas Series if it is a numpy array for rolling functionality
    if isinstance(data, np.ndarray):
        data = pd.Series(data)
    
    # Calculate the rolling mean (Middle Band)
    middle_band = data.rolling(window=window).mean()
    
    # Calculate the rolling standard deviation (use ddof=0 for population std as intended by John Bollinger)
    rolling_std = data.rolling(window=window).std(ddof=0)
    print(f"rolling_std: {rolling_std[-5:]}")

    # Calculate Upper and Lower Bands
    upper_band = middle_band + (rolling_std * num_std)
    lower_band = middle_band - (rolling_std * num_std)
    
    return pd.DataFrame({
        'middle_band': middle_band,
        'upper_band': upper_band,
        'lower_band': lower_band
    })

if __name__ == "__main__":
    # Example: Create a sample array of closing prices (replace with real data)
    # In a real scenario, you'd load this from a CSV or a financial data library like yfinance
    close_prices = np.array([
        29.85, 29.83, 29.90, 30.10, 31.27, 32.00, 31.50, 31.80, 32.10, 32.50,
        32.80, 33.10, 32.90, 33.20, 33.50, 33.80, 33.60, 33.90, 34.20, 34.50,
        34.80, 34.60, 34.90, 35.20, 35.50, 35.80, 35.60, 35.90, 36.20, 36.50
    ])


    # 2. Calculate the Bollinger Bands
    bands = calculate_bollinger_bands(close_prices, window=5, num_std=2)

    # 3. Print the results (NaN values will appear for the first 19 days)
    print(bands.tail())

    # Calculate the bands
    mid, upper, lower = bollinger_bands_numba(close_prices, 5, 2)

    # Print the last few values (initial values will be NaN)
    print(f"Middle Band (last 5): {mid[-5:]}")
    print(f"Upper Band (last 5): {upper[-5:]}")
    print(f"Lower Band (last 5): {lower[-5:]}")

