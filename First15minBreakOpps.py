import numpy as np
import math
import random
from datetime import datetime
from Utilities import slippage

mid_time = datetime.strptime("12:30", "%H:%M").time()
end_time = datetime.strptime("15:10", "%H:%M").time()

def read_from_csv(symbol: str, path='hist\\5min\\'):
    # Read CSV into NumPy arrays
    data = np.genfromtxt(f'{path+symbol}_5min.csv', delimiter=',', dtype=None, names=True, encoding='utf-8')
    dates = np.array([datetime.strptime(d, '%Y-%m-%d').date() for d in data['date']])
    times = np.array([datetime.strptime(t, '%H:%M:%S').time() for t in data['time']])
    highs = data['High']
    lows = data['Low']
    closes = data['Close']
    return symbol, dates, times, highs, lows, closes

def run(*args, **kwargs):
    symbol, dates, times, highs, lows, closes = args
    # print(symbol)

    entry_offset_high = kwargs.get('entry_offset_high', 0.0)
    entry_offset_low = kwargs.get('entry_offset_low', 0.0)
    sl_adjustment = kwargs.get('sl_adjustment', 0.03) * closes[0]
    tp_adjustment = kwargs.get('tp_adjustment', 0.0)
    consider_SL = kwargs.get('consider_SL', "Previous")
    debug = kwargs.get('debug', False)
    use_ema = kwargs.get('use_ema', True)
    ema_period = kwargs.get('ema_period', 40)
    trailing_enabled = kwargs.get('trailing_enabled', False)
    trail_buffer = kwargs.get('trail_buffer', 0.6)

    Margin = kwargs.get('Margin', 100000)
    RR = kwargs.get('RR', 1.48)

    # Calculate 20-day EMA
    span = ema_period
    alpha = 2 / (span + 1)
    ema = np.empty_like(closes)
    ema[0] = closes[0]
    for i in range(1, len(closes)):
        ema[i] = alpha * closes[i] + (1 - alpha) * ema[i - 1]

    # print(ema[75:84], highs[75:84])

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
        date_highs = highs[date_mask]
        date_lows = lows[date_mask]
        date_closes = closes[date_mask]
        date_ema = ema[date_mask]

        sl_adjustment = date_closes[0] * 0.02

        # print(date_indices)

        # Compute initial 15m high and low
        init_15m_high = np.max(date_highs[:3]) + entry_offset_high
        init_15m_low = np.min(date_lows[:3]) - entry_offset_low

        init_15m_high_rounded = slippage(init_15m_high)
        init_15m_low_rounded = slippage(init_15m_low)

        no_of_long_shares = math.floor(Margin / init_15m_high_rounded)
        no_of_short_shares = math.floor(Margin / init_15m_low_rounded)

        daily_pl = 0
        positioned = False
        position = None
        SL = TP = rounded_TP = rounded_SL = None

        for idx in range(3, len(date_indices)):
            current_high = date_highs[idx]
            current_low = date_lows[idx]
            prev_high = date_highs[idx-1]
            prev_low = date_lows[idx-1]
            current_close = date_closes[idx]
            current_ema = date_ema[idx]
            current_time = times[date_indices[idx]]

            if current_time >= mid_time and not positioned:
                break

            if current_time >= end_time and positioned:
                # cancel position
                positioned = False
                if position == "Long":
                    u = random.uniform(max(current_low, (init_15m_low_rounded + SL)/2), min(current_high, (TP + init_15m_low_rounded)/2))
                    daily_pl -= (init_15m_low_rounded - u) * no_of_long_shares
                elif position == "Short":
                    u = random.uniform(max(current_low, (init_15m_high_rounded + TP)/2), min(current_high, (init_15m_high_rounded + SL)/2))
                    daily_pl += (init_15m_high_rounded - u) * no_of_short_shares
                print(f"15:20 Cancel") if debug else None
                break

            # Long entry conditions
            if current_low <= init_15m_low and not positioned and (current_ema > current_close if use_ema else True):
                TP = init_15m_high
                SL = init_15m_low_rounded - (TP - init_15m_low) / RR - sl_adjustment
                TP -= tp_adjustment
                if TP - init_15m_low_rounded >= 0.5 and init_15m_low_rounded - SL >= 0.5:
                    positioned = True
                    position = "Long"
                    # rounded_TP = slippage(TP)
                    # rounded_SL = slippage(SL)
                    no_of_trades += 1
                    if debug:
                        print(f"{current_date} Long entry at {current_time}, SL: {SL}, TP: {TP}")
                else:
                    print("Rejecting trade due to small sl/tp") if debug else None
                    continue

            # Short entry conditions
            elif current_high >= init_15m_high and not positioned and (current_ema < current_close if use_ema else True):
                TP = init_15m_low
                SL = init_15m_high_rounded + (init_15m_high - TP) / RR + sl_adjustment
                TP += tp_adjustment
                if SL - init_15m_high_rounded >= 0.5 and init_15m_high_rounded - TP >= 0.5:
                    positioned = True
                    position = "Short"
                    # rounded_TP = slippage(TP)
                    # rounded_SL = slippage(SL)
                    no_of_trades += 1
                    if debug:
                        print(f"{current_date} Short entry at {current_time}, SL: {SL}, TP: {TP}")
                else:
                    print("Rejecting trade due to small sl/tp") if debug else None
                    continue

            # Exit conditions for Long
            if positioned and position == "Long":
                if current_high >= TP and not trailing_enabled:
                    daily_pl = (slippage(TP) - init_15m_low_rounded) * no_of_long_shares
                    wins += 1
                    positioned = False
                    if debug:
                        print(f"{current_time} TP hit at {TP}")
                    break

                if current_high >= TP and trailing_enabled and current_high - SL > trail_buffer:
                    SL = current_high - trail_buffer
                    # rounded_SL = slippage(SL)
                    if debug:
                        print(f"{current_time} updated Trail SL: {SL}")
                elif current_low <= SL:
                    daily_pl = (slippage(SL) - init_15m_low_rounded) * no_of_long_shares
                    if trailing_enabled and current_high:
                        wins += 1
                    positioned = False
                    if debug:
                        print(f"{current_time} SL hit at {SL}")
                    break

            # Exit conditions for Short
            elif positioned and position == "Short":
                if current_low <= TP  and not trailing_enabled:
                    daily_pl = (init_15m_high_rounded - slippage(TP)) * no_of_short_shares
                    wins += 1
                    positioned = False
                    if debug:
                        print(f"{current_time} TP hit at {TP}")
                        break

                if current_low <= TP and trailing_enabled and SL - current_low > trail_buffer:
                    SL = current_low + trail_buffer
                    # rounded_SL = slippage(SL)
                    if debug:
                        print(f"{current_time} updated Trail SL: {SL}")
                elif current_high >= SL:
                    daily_pl = (init_15m_high_rounded - slippage(SL)) * no_of_short_shares
                    if trailing_enabled and daily_pl > 0:
                        wins += 1
                    positioned = False
                    if debug:
                        print(f"{current_time} SL hit at {SL}")
                    break

        net_pl += daily_pl
        Margin += daily_pl
        if debug:
            print(f"{current_date} Daily PL: {round(daily_pl, 2)}\n")

    rounded_net_pl = round(net_pl, 2)
    rounded_wins_pct = round(wins*100/no_of_trades, 2)
    # print(f"{symbol} Net PL: {rounded_net_pl} ({net_pl/1000:.2f}%), Days: {days}, Total Trades: {no_of_trades}, Wins: {wins} ({rounded_wins_pct}%)")

    return symbol, rounded_net_pl, rounded_wins_pct
