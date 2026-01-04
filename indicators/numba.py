import numpy as np
from numba import njit

@njit
def calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    alpha = 2 / (period + 1)
    ema = np.empty_like(data)
    ema[0] = data[0]  # seed with first price
    
    for i in range(1, data.shape[0]):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
    
    return ema

@njit
def calculate_macd_histogram(prices, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    return macd_line - signal_line  # Histogram

@njit
def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int=14) -> np.ndarray:
    atr = np.empty_like(close)
    tr = np.empty_like(close)
    
    tr[0] = high[0] - low[0]
    for i in range(1, close.shape[0]):
        h_l = high[i] - low[i]
        h_pc = abs(high[i] - close[i - 1])
        l_pc = abs(low[i] - close[i - 1])
        tr[i] = max(h_l, h_pc, l_pc)

    # First ATR point is SMA of first `period` TRs
    atr[:period] = np.nan
    atr[period - 1] = np.mean(tr[:period])
    
    # Rest: EMA-style smoothing
    alpha = 1 / period
    for i in range(period, close.shape[0]):
        atr[i] = alpha * tr[i] + (1 - alpha) * atr[i - 1]
    
    return atr

@njit
def calculate_supertrend(high, low, close, period=10, multiplier=3.0):
    n = len(close)
    
    # --- ATR Calculation ---
    atr = calculate_atr(high, low, close, period)

    # --- Supertrend Calculation ---
    upperband = np.empty(n)
    lowerband = np.empty(n)
    trend = np.empty(n, dtype=np.int8)

    for i in range(n):
        upperband[i] = ((high[i] + low[i]) / 2) + multiplier * atr[i]
        lowerband[i] = ((high[i] + low[i]) / 2) - multiplier * atr[i]

    trend[:] = 1  # Default to uptrend
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
def calculate_adx(high, low, close, period=14):
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

    return adx  # ADX values: higher = stronger trend

@njit
def calculate_vwap(high, low, close, volume):
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
def calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
    n = data.shape[0]
    sma = np.empty(n)
    sma[:period-1] = np.nan

    window_sum = 0.0
    for i in range(period):
        window_sum += data[i]
    sma[period - 1] = window_sum / period

    for i in range(period, n):
        window_sum += data[i] - data[i - period]
        sma[i] = window_sum / period

    return sma

@njit
def calculate_ema_slope_simple(ema_values: np.ndarray, lookback: int = 10) -> np.ndarray:
    n = len(ema_values)
    slopes = np.empty(n)
    
    for i in range(lookback):
        slopes[i] = np.nan  # Fill front NaNs
    
    for i in range(lookback, n):
        slopes[i] = (ema_values[i] - ema_values[i - lookback]) / lookback

    return slopes

@njit
def calculate_ema_slope_linreg(ema_values: np.ndarray, lookback: int = 10) -> np.ndarray:
    n = len(ema_values)
    slopes = np.empty(n)
    x = np.arange(lookback)
    x_mean = np.mean(x)
    x_demean = x - x_mean
    denom = np.sum(x_demean ** 2)

    for i in range(lookback):
        slopes[i] = np.nan

    for i in range(lookback, n):
        window = ema_values[i - lookback:i]
        y_mean = np.mean(window)
        y_demean = window - y_mean
        slope = np.sum(x_demean * y_demean) / denom
        slopes[i] = slope

    return slopes

@njit
def calculate_ema_slope(ema_values: np.ndarray, lookback: int=10, method: str='simple') -> np.ndarray:
    match method:
        case 'simple':
            return calculate_ema_slope_simple(ema_values, lookback)
        case 'linreg':
            return calculate_ema_slope_linreg(ema_values, lookback)
        case _:
            raise ValueError("Invalid method. Use 'simple' or 'linreg'.")

@njit
def daily_rolling_median_atr(atr: np.ndarray, candles_per_day: int = 75, window_days: int = 30) -> np.ndarray:
    n_candles = len(atr)
    n_days = n_candles // candles_per_day
    median_atr_per_day = np.full(n_days, np.nan)

    for i in range(window_days, n_days):
        start_idx = (i - window_days) * candles_per_day
        end_idx = i * candles_per_day
        window = atr[start_idx:end_idx]
        median_atr_per_day[i] = np.nanmedian(window)

    # Broadcast per-day median ATR back to per-candle resolution
    full_median_array = np.empty(n_candles)
    for i in range(n_days):
        day_start = i * candles_per_day
        day_end = day_start + candles_per_day
        val = median_atr_per_day[i] if i < len(median_atr_per_day) else np.nan
        for j in range(day_start, min(day_end, n_candles)):
            full_median_array[j] = val

    return full_median_array

