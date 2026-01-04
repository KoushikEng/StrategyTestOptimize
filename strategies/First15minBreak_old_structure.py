import numpy as np
import math
import random
from datetime import datetime
from Utilities import slippage
from indicators.numba import calculate_ema, calculate_sma, calculate_ema_slope, calculate_atr
from indicators.vectorized import vectorized_atr

mid_time = datetime.strptime("12:30", "%H:%M").time()
end_time = datetime.strptime("15:10", "%H:%M").time()

def read_from_csv(symbol: str, path: str):
    # Read CSV into NumPy arrays
    data = np.genfromtxt(f'{path+symbol}_5min.csv', delimiter=',', dtype=None, names=True, encoding='utf-8')
    dates = np.array([datetime.strptime(d, '%Y-%m-%d').date() for d in data['date']])
    times = np.array([datetime.strptime(t, '%H:%M:%S').time() for t in data['time']])
    opens = data['Open']
    highs = data['High']
    lows = data['Low']
    closes = data['Close']
    volume = data['Volume']
    return symbol, dates, times, opens, highs, lows, closes, volume

def run(*args, **kwargs):
    symbol, dates, times, opens, highs, lows, closes, volume = args

    DEBUG = True
    CONFIRM_EMA = True
    CONFIRM_EMA_SLOPE = True
    ENABLED_TRAILING = True
    EMA_PERIOD = 20
    EMA_SLOPE_PERIOD = 15
    TRAIL_AMOUNT = 0.6
    CONFIRM_VOLUME = True
    
    SL_MULTIPLIER = 2.5
    TP_MULTIPLIER = 3.0
    
    f = open(f"results/{symbol}_debug.txt", 'w')

    Margin = kwargs.get('Margin', 100000)

    vol_span = 20
    vol_ema = calculate_ema(volume, vol_span)

    # Calculate 20-day EMA
    ema = calculate_ema(closes, EMA_PERIOD) if CONFIRM_EMA else np.zeros_like(closes)
    ema_slope = calculate_ema_slope(ema, EMA_SLOPE_PERIOD) if CONFIRM_EMA and CONFIRM_EMA_SLOPE else np.zeros_like(closes)
    atr = vectorized_atr(highs, lows, closes)

    # Group data by date
    unique_dates = np.unique(dates)
    net_pl = 0
    days = 0
    no_of_trades = 0
    wins = 0

    for current_date in unique_dates:
        days += 1

        # Get data for the current date
        date_mask = dates == current_date
        date_indices = np.where(date_mask)[0]
        date_open = opens[date_mask]
        date_highs = highs[date_mask]
        date_lows = lows[date_mask]
        date_closes = closes[date_mask]
        date_volume = volume[date_mask]
        date_ema = ema[date_mask]
        date_ema_slope = ema_slope[date_mask]
        date_volume_ema = vol_ema[date_mask]
        date_atr = atr[date_mask]
        
        # sl_adjustment = date_closes[0]

        # print(date_indices)

        # Compute initial 15m high and low
        init_15m_high = np.max(date_highs[:3])
        init_15m_low = np.min(date_lows[:3])

        init_15m_high_rounded = slippage(init_15m_high)
        init_15m_low_rounded = slippage(init_15m_low)

        no_of_long_shares = math.floor(Margin / init_15m_high_rounded)
        no_of_short_shares = math.floor(Margin / init_15m_low_rounded)

        daily_pl = 0
        positioned = False
        position = None
        SL = TP = rounded_TP = rounded_SL = None
        entry_price = None

        for idx in range(3, len(date_indices)):
            current_high = date_highs[idx]
            current_low = date_lows[idx]
            current_close = date_closes[idx]
            prev_close = date_closes[idx-1]
            
            current_volume = date_volume[idx]
            current_ema = date_ema[idx-1]
            current_ema_slope = date_ema_slope[idx-1]
            current_volume_ema = date_volume_ema[idx-1]
            current_atr = date_atr[idx - 1]
            
            current_time = times[date_indices[idx]]
            
            # if DEBUG:
            #     print(current_atr)

            if current_time >= mid_time and not positioned:
                break

            if current_time >= end_time and positioned:
                # cancel position
                positioned = False
                if position == "Long":
                    u = random.uniform(max(current_low, (entry_price + SL)/2), min(current_high, (TP + entry_price)/2))
                    daily_pl -= (entry_price - u) * no_of_long_shares
                elif position == "Short":
                    u = random.uniform(max(current_low, (entry_price + TP)/2), min(current_high, (entry_price + SL)/2))
                    daily_pl += (entry_price - u) * no_of_short_shares
                print(f"15:20 Cancel", file=f) if DEBUG else None
                break

            # Long entry conditions
            if current_high >= init_15m_high and not positioned and (current_ema < prev_close and current_ema_slope > 0 if CONFIRM_EMA else True) and (current_volume > 1.5 * current_volume_ema if CONFIRM_VOLUME else True):
                # SL = prev_low if consider_SL == "Previous" else current_low
                # TP = init_15m_high_rounded + RR * (init_15m_high - SL) - current_open * tp_adjustment
                # SL -= current_open * sl_adjustment
                ABS_SL = SL_MULTIPLIER * current_atr
                ABS_TP = TP_MULTIPLIER * current_atr
                entry_price = random.uniform(init_15m_high, (init_15m_high + current_close)/2)
                no_of_long_shares = int(Margin/entry_price)
                SL = entry_price - ABS_SL
                TP = entry_price + ABS_TP
                if ABS_SL >= 0.5 and ABS_TP >= 0.5:
                    positioned = True
                    position = "Long"
                    rounded_TP = slippage(TP)
                    rounded_SL = slippage(SL)
                    no_of_trades += 1
                    if DEBUG:
                        print(f"{current_date} Long entry at {current_time}, SL: {SL}, TP: {TP}", file=f)
                else:
                    print("Rejecting trade due to small sl/tp", file=f) if DEBUG else None
                    continue

            # Short entry conditions
            elif current_low <= init_15m_low and not positioned and (current_ema > prev_close and current_ema_slope < 0 if CONFIRM_EMA else True) and (current_volume > 1.5 * current_volume_ema if CONFIRM_VOLUME else True):
                # SL = prev_high if consider_SL == "Previous" else current_high
                # TP = init_15m_low_rounded - RR * (SL - init_15m_low) + current_open * tp_adjustment
                # SL += current_open * sl_adjustment
                ABS_SL = SL_MULTIPLIER * current_atr
                ABS_TP = TP_MULTIPLIER * current_atr
                entry_price = random.uniform((init_15m_low + current_close)/2, init_15m_low)
                no_of_short_shares = int(Margin/entry_price)
                SL = entry_price + ABS_SL
                TP = entry_price - ABS_TP
                if ABS_SL >= 0.5 and ABS_TP >= 0.5:
                    positioned = True
                    position = "Short"
                    rounded_TP = slippage(TP)
                    rounded_SL = slippage(SL)
                    no_of_trades += 1
                    if DEBUG:
                        print(f"{current_date} Short entry at {current_time}, SL: {SL}, TP: {TP}", file=f)
                else:
                    print("Rejecting trade due to small sl/tp", file=f) if DEBUG else None
                    continue

            # Exit conditions for Long
            if positioned and position == "Long":
                if current_high >= TP and not ENABLED_TRAILING:
                    daily_pl += (rounded_TP - entry_price) * no_of_long_shares
                    wins += 1
                    positioned = False
                    if DEBUG:
                        print(f"{current_time} TP hit at {TP}", file=f)
                    break

                if current_high >= TP and ENABLED_TRAILING and current_high - SL > TRAIL_AMOUNT:
                    SL = current_high - TRAIL_AMOUNT
                    rounded_SL = slippage(SL)
                    if DEBUG:
                        print(f"{current_time} updated Trail SL: {SL}", file=f)
                elif current_low <= SL:
                    daily_pl += (rounded_SL - entry_price) * no_of_long_shares
                    if ENABLED_TRAILING and daily_pl > 0:
                        wins += 1
                    positioned = False
                    if DEBUG:
                        print(f"{current_time} SL hit at {SL}", file=f)
                    break

            # Exit conditions for Short
            elif positioned and position == "Short":
                if current_low <= TP  and not ENABLED_TRAILING:
                    daily_pl += (entry_price - rounded_TP) * no_of_short_shares
                    wins += 1
                    positioned = False
                    if DEBUG:
                        print(f"{current_time} TP hit at {TP}", file=f)
                        break

                elif current_low <= TP and ENABLED_TRAILING and SL - current_low > TRAIL_AMOUNT:
                    SL = current_low + TRAIL_AMOUNT
                    rounded_SL = slippage(SL)
                    if DEBUG:
                        print(f"{current_time} updated Trail SL: {SL}", file=f)
                elif current_high >= SL:
                    daily_pl += (entry_price - rounded_SL) * no_of_short_shares
                    if ENABLED_TRAILING and daily_pl > 0:
                        wins += 1
                    positioned = False
                    if DEBUG:
                        print(f"{current_time} SL hit at {SL}", file=f)
                    break

        net_pl += daily_pl
        Margin += daily_pl
        if DEBUG:
            print(f"{current_date} Daily PL: {round(daily_pl, 2)}\n", file=f)

    rounded_net_pl = round(net_pl, 2)
    rounded_wins_pct = round(wins*100/no_of_trades, 2) if no_of_trades > 0 else 0.0
    if DEBUG:
        print(f"{symbol} Net PL: {rounded_net_pl} ({net_pl/1000:.2f}%), Days: {days}, Total Trades: {no_of_trades}, Wins: {wins} ({rounded_wins_pct}%)\n\n", file=f)

    f.close()
    return symbol, rounded_net_pl, rounded_wins_pct


