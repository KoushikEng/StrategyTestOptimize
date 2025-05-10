import numpy as np
from datetime import datetime
from Utilities import slippage
from numba_calculations import calculate_ema, calculate_sma, calculate_ema_slope, calculate_atr
from numba import njit
from vectorized_calculations import vectorized_atr
from enum import Enum

mid_time = datetime.strptime("12:30", "%H:%M").time()
end_time = datetime.strptime("15:10", "%H:%M").time()

class POSITION_TYPE(Enum):
    LONG = 1
    SHORT = -1

@njit
def calculate_qty(margin: float, sl: float, price: float, risk_amount : float=0.02) -> int:
    if margin <= 0.0  or sl <= 0.0 or price <= 0.0:
        return 0
    risk_per_trade = margin * risk_amount
    qty = min(risk_per_trade / sl, margin / price)
    return int(qty)

def get_fill_price(breakout_level, current_low, current_high, current_open, atr_value, spread=0.0002, is_long=True):
    """
    Brutally realistic backtest fills. Assumes:
    - If breakout level is within candle range -> filled at worst possible price
    - Otherwise -> aggressive slippage
    """
    spread = breakout_level * spread
    
    if is_long:
        # Case 1: Breakout level was touched this candle
        if current_low <= breakout_level <= current_high:
            # You get filled at breakout_level + 0.3*ATR (worst-case within candle)
            return breakout_level + max(0.25 * atr_value, spread)
        
        # Case 2: Price never touched breakout (slipped away)
        else:
            # Penalty = distance from breakout to open + 0.5*ATR
            slippage = max(current_open - breakout_level, 0) + 0.25 * atr_value
            return breakout_level + slippage + spread
    else:
        # Short logic (mirror image)
        if current_low <= breakout_level <= current_high:
            return breakout_level - max(0.25 * atr_value, spread)
        else:
            slippage = max(breakout_level - current_open, 0) + 0.25 * atr_value
            return breakout_level - slippage - spread

def exit_at_market_close(position_type: POSITION_TYPE, 
                        entry_price: float,
                        current_low: float,
                        current_high: float,
                        current_close: float,
                        current_volume: float,
                        avg_volume: float,
                        atr_value: float,
                        SL: float,
                        position_size: float) -> float:
    """
    Realistic market-close exit for intraday 5m strategies.
    
    Returns:
        Tuple: (exit_price, pnl)
    """
    # Calculate volume ratio (0.5-1.5 range)
    vol_ratio = min(max(current_volume / avg_volume, 0.5), 1.5)
    
    if position_type == POSITION_TYPE.LONG:
        # Volume-weighted exit price (70% close, 30% low, adjusted by volume)
        exit_price = (current_close*0.7 + current_low*0.3) * (1 - 0.1*(1 - vol_ratio))
        
        # ATR-based protection (minimum fill improvement)
        min_fill = current_close - 0.3 * atr_value
        exit_price = max(exit_price, min_fill, SL)
        
        pnl = (exit_price - entry_price) * position_size
    
    elif position_type == POSITION_TYPE.SHORT:
        # Volume-weighted exit price (70% close, 30% high)
        exit_price = (current_close*0.7 + current_high*0.3) * (1 + 0.1*(1 - vol_ratio))
        
        # ATR-based protection
        max_fill = current_close + 0.3 * atr_value
        exit_price = min(exit_price, max_fill, SL)
        
        pnl = (entry_price - exit_price) * position_size
    
    return exit_price, pnl

def should_trade_based_on_ema(current_price: float, 
                            last_ema: float, 
                            last_ema_slope: float, 
                            atr_value: float,
                            side: POSITION_TYPE = POSITION_TYPE.LONG) -> bool:
    """
    Enhanced EMA filter with volatility-adjusted slope requirements.
    
    Args:
        current_price: Latest closing price
        last_ema: Most recent EMA value
        last_ema_slope: Slope of EMA (in price units per period)
        atr_value: Current ATR for dynamic thresholding
        side: POSITION_TYPE.LONG or POSITION_TYPE.SHORT
        
    Returns:
        bool: True if EMA conditions are met
    """
    # --- Fail Safes ---
    if not last_ema or not last_ema_slope or atr_value <= 0:
        return False
    
    # --- Dynamic Slope Threshold (ATR-Adaptive) ---
    # Minimum slope = 10% of ATR (avoids false signals in choppy markets)
    min_slope = 0.0 * atr_value # set to 0 for testing
    
    if side == POSITION_TYPE.LONG:
        price_condition = current_price > last_ema
        slope_condition = last_ema_slope > min_slope  # Stronger uptrend required
        return price_condition and slope_condition
        
    elif side == POSITION_TYPE.SHORT:
        price_condition = current_price < last_ema
        slope_condition = last_ema_slope < -min_slope  # Stronger downtrend required
        return price_condition and slope_condition
        
    return False

def should_trade_based_on_vol(current_vol :int, avg_vol :int, vol_multiplier: float=1.5) -> bool:
    if not current_vol or not avg_vol:
        return False
    return current_vol > vol_multiplier * avg_vol

def run(*args, **kwargs):
    symbol, dates, times, opens, highs, lows, closes, volume = args
    
    f = open(f"results/{symbol}_debug.txt", 'w')

    # Constant parameters
    DEBUG = True
    
    ENABLED_TRAILING = kwargs.get('trail', False)
    
    EMA_PERIOD = int(kwargs.get('ema', 20))
    EMA_SLOPE_PERIOD = int(kwargs.get('ema_slope', 15))
    AVG_VOL_SPAN = int(kwargs.get('avg_vol', 20))
    ATR_PERIOD = int(kwargs.get('atr', 14))
    
    ATR_TRAIL_MULTIPLIER = float(kwargs.get('trail_multi', 0.5))
    ATR_SL_MULTIPLIER = np.float64(kwargs.get('sl_multi', 2.5))
    ATR_TP_MULTIPLIER = np.float64(kwargs.get('tp_multi', 3.0))
    VOL_MULTIPLIER = float(kwargs.get('vol_multi', 1.5))

    # --- Indicators ---
    avg_vol = calculate_ema(volume, AVG_VOL_SPAN)
    ema = calculate_ema(closes, EMA_PERIOD)
    ema_slope = calculate_ema_slope(ema, EMA_SLOPE_PERIOD, method='simple')
    atr = calculate_atr(highs, lows, closes, ATR_PERIOD)
    
    # --- Trading Logic ---
    returns = []
    
    Margin = kwargs.get('Margin', 100000)

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
        date_opens = opens[date_mask]
        date_highs = highs[date_mask]
        date_lows = lows[date_mask]
        date_closes = closes[date_mask]
        date_volume = volume[date_mask]
        date_ema = ema[date_mask]
        date_ema_slope = ema_slope[date_mask]
        date_avg_vol = avg_vol[date_mask]
        date_atr = atr[date_mask]

        # Compute initial 15m high and low
        first_15m_high = np.max(date_highs[:3])
        first_15m_low = np.min(date_lows[:3])

        no_of_long_shares = 0
        no_of_short_shares = 0

        daily_pl = 0
        in_position = False
        position_type = None
        SL = TP = None
        entry_price = None
        
        is_brokeout = False
        is_confirmed_vol = False

        for idx in range(3, len(date_indices)):
            current_open = date_opens[idx]
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

            if current_time >= mid_time and not in_position:
                break

            if current_time >= end_time and in_position:
                exit_price, pnl = exit_at_market_close(
                    position_type=position_type,
                    entry_price=entry_price,
                    current_low=current_low,
                    current_high=current_high,
                    current_close=current_close,
                    current_volume=current_volume,
                    avg_volume=current_avg_vol,
                    atr_value=current_atr,
                    SL=SL,
                    position_size=no_of_long_shares if position_type == POSITION_TYPE.LONG else no_of_short_shares
                )
                
                daily_pl += pnl
                in_position = False
                
                if DEBUG:
                    print(f"{current_time} - Market Close Exit | "
                        f"Position: {position_type} | "
                        f"Exit: {exit_price:.5f} | "
                        f"Vol Ratio: {current_volume/current_avg_vol:.2f}x | "
                        f"PnL: {pnl:.2f}", 
                        file=f)
                break

            # Long entry conditions
            if ((current_high > first_15m_high and current_close > prev_close and not in_position) # original condition
                and should_trade_based_on_ema(current_close, last_ema, last_ema_slope, current_atr) # ema condition
                and should_trade_based_on_vol(current_volume, current_avg_vol, VOL_MULTIPLIER) # volume condition
                ):
                ABS_SL = ATR_SL_MULTIPLIER * current_atr
                ABS_TP = ATR_TP_MULTIPLIER * current_atr
                entry_price = get_fill_price(first_15m_high, current_low, current_high, current_open, current_atr)
                no_of_long_shares = calculate_qty(Margin, ABS_SL, entry_price)
                SL = entry_price - ABS_SL
                TP = entry_price + ABS_TP
                if ABS_TP >= 0.5 and ABS_SL >= 0.5 and no_of_long_shares > 0:
                    in_position = True
                    position_type = POSITION_TYPE.LONG
                    no_of_trades += 1
                    if DEBUG:
                        print(f"{current_date} Long entry at {current_time} @{entry_price:.2f}, qty: {no_of_long_shares}, SL: {SL:.2f}, TP: {TP:.2f}", file=f)
                else:
                    print("Rejecting trade due to small sl/tp", file=f) if DEBUG else None
                
                continue

            # Short entry conditions
            elif ((current_low < first_15m_low and current_close < prev_close and not in_position) # original condition
                and should_trade_based_on_ema(current_close, last_ema, last_ema_slope, current_atr, POSITION_TYPE.SHORT) # ema condition
                and should_trade_based_on_vol(current_volume, current_avg_vol, VOL_MULTIPLIER) # volume condition
                ):
                ABS_SL = ATR_SL_MULTIPLIER * current_atr
                ABS_TP = ATR_TP_MULTIPLIER * current_atr
                entry_price = get_fill_price(first_15m_low, current_low, current_high, current_open, current_atr, is_long=False)
                no_of_short_shares = calculate_qty(Margin, ABS_SL, entry_price)
                SL = entry_price + ABS_SL
                TP = entry_price - ABS_TP
                if ABS_TP >= 0.5 and ABS_SL >= 0.5 and no_of_short_shares > 0:
                    in_position = True
                    position_type = POSITION_TYPE.SHORT
                    no_of_trades += 1
                    if DEBUG:
                        print(f"{current_date} Short entry at {current_time} @{entry_price:.2f}, qty: {no_of_short_shares}, SL: {SL:.2f}, TP: {TP:.2f}", file=f)
                else:
                    print("Rejecting trade due to small sl/tp", file=f) if DEBUG else None
                
                continue

            # Exit conditions for Long
            if in_position and position_type == POSITION_TYPE.LONG:
                # Take Profit Logic
                if current_high >= TP:
                    if not ENABLED_TRAILING:
                        daily_pl += (TP - entry_price) * no_of_long_shares  # TP is <= current_high by definition
                        wins += 1
                        in_position = False
                        if DEBUG: print(f"{current_time} TP hit at {TP:.4f}", file=f)
                        break
                    
                    # Trailing Stop Logic
                    elif ENABLED_TRAILING:
                        new_sl = current_high - (ATR_TRAIL_MULTIPLIER * current_atr)
                        if new_sl > SL:  # Only tighten the SL
                            SL = new_sl
                            if DEBUG: print(f"{current_time} Trail SL updated to {SL:.4f}", file=f)
                
                # Stop Loss Logic
                if current_low <= SL:
                    daily_pl += (SL - entry_price) * no_of_long_shares  # SL is >= current_low when condition triggers
                    if ENABLED_TRAILING and (SL - entry_price) > 0:
                        wins += 1  # Only count as win if profitable
                    in_position = False
                    if DEBUG: print(f"{current_time} SL hit at {SL:.4f}", file=f)
                    break

            # Exit conditions for Short (identical cleanup)
            elif in_position and position_type == POSITION_TYPE.SHORT:
                if current_low <= TP:
                    if not ENABLED_TRAILING:
                        daily_pl += (entry_price - TP) * no_of_short_shares
                        wins += 1
                        in_position = False
                        if DEBUG: print(f"{current_time} TP hit at {TP:.4f}", file=f)
                        break
                    
                    elif ENABLED_TRAILING:
                        new_sl = current_low + (ATR_TRAIL_MULTIPLIER * current_atr)
                        if new_sl < SL:  # Only tighten the SL
                            SL = new_sl
                            if DEBUG: print(f"{current_time} Trail SL updated to {SL:.4f}", file=f)
                
                if current_high >= SL:
                    daily_pl += (entry_price - SL) * no_of_short_shares
                    if ENABLED_TRAILING and (entry_price - SL) > 0:
                        wins += 1
                    in_position = False
                    if DEBUG: print(f"{current_time} SL hit at {SL:.4f}", file=f)
                    break

        net_pl += daily_pl
        Margin += daily_pl
        returns.append(daily_pl)
        if DEBUG:
            print(f"{current_date} Daily PL: {round(daily_pl, 2)}\n", file=f)

    rounded_net_pl = round(net_pl, 2)
    rounded_wins_pct = round(wins*100/no_of_trades, 2) if no_of_trades > 0 else 0.0
    
    if DEBUG:
        print(f"{symbol} Net PL: {rounded_net_pl} ({net_pl/1000:.2f}%), Days: {days}, Total Trades: {no_of_trades}, Wins: {wins} ({rounded_wins_pct}%)\n", file=f)

    f.close()
    
    return symbol, np.array(returns, dtype=np.float64), rounded_wins_pct


