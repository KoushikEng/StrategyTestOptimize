import numpy as np
import math
import random
from datetime import datetime
from Utilities import slippage
from numba_calculations import calculate_ema, calculate_sma, calculate_ema_slope, calculate_atr
from numba import njit
from vectorized_calculations import vectorized_atr

mid_time = datetime.strptime("12:30", "%H:%M").time()
end_time = datetime.strptime("15:10", "%H:%M").time()

@njit
def calculate_qty(margin: float, sl: float, price: float, risk_amount : float=0.02) -> int:
    if margin <= 0.0  or sl <= 0.0 or price <= 0.0:
        return 0
    risk_per_trade = margin * risk_amount
    qty = min(risk_per_trade / sl, margin / price)
    return int(qty)

def run(*args, **kwargs):
    symbol, dates, times, opens, highs, lows, closes, volume = args
    
    f = open(f"results/{symbol}_debug.txt", 'w')

    # Constant parameters
    DEBUG = True
    
    CONFIRM_EMA = True
    CONFIRM_EMA_SLOPE = True
    ENABLED_TRAILING = kwargs.get('trail', False)
    CONFIRM_VOLUME = True
    CONFIRM_ATR = True
    
    ATR_TRAIL_MULTIPLIER = float(kwargs.get('trail_multi', 0.5))
    EMA_PERIOD = int(kwargs.get('ema', 20))
    EMA_SLOPE_PERIOD = int(kwargs.get('ema_slope', 15))
    AVG_VOL_SPAN = int(kwargs.get('avg_vol', 20))
    ATR_PERIOD = int(kwargs.get('atr', 14))
    
    ATR_SL_MULTIPLIER = np.float64(kwargs.get('sl_multi', 2.5))
    ATR_TP_MULTIPLIER = np.float64(kwargs.get('tp_multi', 3.0))
    
    VOL_MULTIPLIER = float(kwargs.get('vol_multi', 1.5))
    
    def should_trade_based_on_ema(current_price :float, last_ema :float, last_ema_slope :float, side :str="long") -> bool:
        if not CONFIRM_EMA:
            return True
        if not last_ema or not last_ema_slope:
            return False
        if side == "long":
            return last_ema < current_price and (last_ema_slope > 0 if CONFIRM_EMA_SLOPE else True)
        elif side == "short":
            return last_ema > current_price and (last_ema_slope < 0 if CONFIRM_EMA_SLOPE else True)
        
        return False
    
    def should_trade_based_on_vol(current_vol :int, avg_vol :int) -> bool:
        if not CONFIRM_VOLUME:
            return True
        if not current_vol or not avg_vol:
            return False
        return current_vol > VOL_MULTIPLIER * avg_vol

    Margin = kwargs.get('Margin', 100000)

    avg_vol = calculate_ema(volume, AVG_VOL_SPAN)
    ema = calculate_ema(closes, EMA_PERIOD) if CONFIRM_EMA else np.zeros_like(closes)
    ema_slope = calculate_ema_slope(ema, EMA_SLOPE_PERIOD, method='simple') if CONFIRM_EMA and CONFIRM_EMA_SLOPE else np.zeros_like(closes)
    atr = calculate_atr(highs, lows, closes, ATR_PERIOD) if CONFIRM_ATR else np.zeros_like(closes)
    
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
        date_volume = volume[date_mask]
        date_ema = ema[date_mask]
        date_ema_slope = ema_slope[date_mask]
        date_avg_vol = avg_vol[date_mask]
        date_atr = atr[date_mask]

        # Compute initial 15m high and low
        init_15m_high = np.max(date_highs[:3])
        init_15m_low = np.min(date_lows[:3])

        init_15m_high_rounded = slippage(init_15m_high)
        init_15m_low_rounded = slippage(init_15m_low)

        no_of_long_shares = 0
        no_of_short_shares = 0

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
            last_ema = date_ema[idx-1]
            last_ema_slope = date_ema_slope[idx-1]
            current_avg_vol = date_avg_vol[idx-1]
            current_atr = date_atr[idx - 1]
            
            current_time = times[date_indices[idx]]

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
            if ((current_high > init_15m_high and not positioned) # original condition
                and should_trade_based_on_ema(prev_close, last_ema, last_ema_slope) # ema condition
                and should_trade_based_on_vol(current_volume, current_avg_vol) # volume condition
                ):
                ABS_SL = ATR_SL_MULTIPLIER * current_atr
                ABS_TP = ATR_TP_MULTIPLIER * current_atr
                entry_price = random.uniform(init_15m_high, (init_15m_high + current_close)/2)
                no_of_long_shares = calculate_qty(Margin, ABS_SL, entry_price)
                SL = entry_price - ABS_SL
                TP = entry_price + ABS_TP
                if ABS_TP >= 0.5 and ABS_SL >= 0.5 and no_of_long_shares > 0:
                    positioned = True
                    position = "Long"
                    rounded_TP = slippage(TP)
                    rounded_SL = slippage(SL)
                    no_of_trades += 1
                    if DEBUG:
                        print(f"{current_date} Long entry at {current_time} @{entry_price:.2f}, qty: {no_of_long_shares}, SL: {SL:.2f}, TP: {TP:.2f}", file=f)
                else:
                    print("Rejecting trade due to small sl/tp", file=f) if DEBUG else None
                    continue

            # Short entry conditions
            elif ((current_low < init_15m_low and not positioned) # original condition
                and should_trade_based_on_ema(prev_close, last_ema, last_ema_slope, "short") # ema condition
                and should_trade_based_on_vol(current_volume, current_avg_vol) # volume condition
                ):
                # SL = prev_high if consider_SL == "Previous" else current_high
                # TP = init_15m_low_rounded - RR * (SL - init_15m_low) + current_open * tp_adjustment
                # SL += current_open * sl_adjustment
                ABS_SL = ATR_SL_MULTIPLIER * current_atr
                ABS_TP = ATR_TP_MULTIPLIER * current_atr
                entry_price = random.uniform((init_15m_low + current_close)/2, init_15m_low)
                no_of_short_shares = calculate_qty(Margin, ABS_SL, entry_price)
                SL = entry_price + ABS_SL
                TP = entry_price - ABS_TP
                # no_of_short_shares = calculate_qty(Margin, ABS_SL, RISK_AMOUNT)
                if ABS_TP >= 0.5 and ABS_SL >= 0.5 and no_of_short_shares > 0:
                    positioned = True
                    position = "Short"
                    rounded_TP = slippage(TP)
                    rounded_SL = slippage(SL)
                    no_of_trades += 1
                    if DEBUG:
                        print(f"{current_date} Short entry at {current_time} @{entry_price:.2f}, qty: {no_of_short_shares}, SL: {SL:.2f}, TP: {TP:.2f}", file=f)
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

                if current_high >= TP and ENABLED_TRAILING and current_high - SL > (trail_amount := ATR_TRAIL_MULTIPLIER * current_atr):
                    SL = current_high - trail_amount
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

                elif current_low <= TP and ENABLED_TRAILING and SL - current_low > (trail_amount := ATR_TRAIL_MULTIPLIER * current_atr):
                    SL = current_low + trail_amount
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
        print(f"{symbol} Net PL: {rounded_net_pl} ({net_pl/1000:.2f}%), Days: {days}, Total Trades: {no_of_trades}, Wins: {wins} ({rounded_wins_pct}%)\n", file=f)

    f.close()
    
    return symbol, rounded_net_pl, rounded_wins_pct


