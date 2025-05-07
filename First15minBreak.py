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

def get_fill_price(breakout_level: float, 
                  current_low: float, 
                  current_high: float, 
                  current_open: float,
                  atr_value: float, 
                  spread: float = 0.0002,
                  is_long: bool = True) -> float:
    """
    Calculates realistic fill price for 5m breakout strategies.
    
    Args:
        breakout_level: Price level to trigger entry (e.g. 15min high)
        current_low/current_high: Candle's price range
        current_open: Candle's open price
        atr_value: Current ATR (14-period recommended)
        spread: Broker spread (0.02% for FX, 0.1% for crypto)
        is_long: True for long entries, False for shorts
        
    Returns:
        Realistic fill price with volatility-adjusted slippage
    """
    # --- Hard Limits for 5m Trading ---
    MIN_SLIPPAGE = 0.0005  # Minimum 0.05% slippage (even in calm markets)
    MAX_SLIPPAGE_PCT = 0.75  # Never pay more than 75% of ATR in slippage
    
    if is_long:
        # Long entry logic
        effective_breakout = max(breakout_level, current_open)
        
        # Case 1: Got filled at breakout (ideal scenario)
        if current_low <= effective_breakout <= current_high:
            return effective_breakout * (1 + spread)
        
        # Case 2: Slipped entry (price blasted through)
        else:
            # Calculate overshoot ratio (how violently price moved)
            overshoot_ratio = (current_high - effective_breakout) / atr_value
            
            # Base slippage + volatility penalty (capped at MAX_SLIPPAGE_PCT)
            slippage_pct = min(0.25 + 0.3 * overshoot_ratio, MAX_SLIPPAGE_PCT)
            
            # Apply minimum slippage guarantee
            slippage = max(atr_value * slippage_pct, effective_breakout * MIN_SLIPPAGE)
            
            # Don't exceed candle's high
            fill_price = effective_breakout * (1 + spread) + min(slippage, current_high - effective_breakout)
            return round(fill_price, 6)  # Avoid floating point precision issues
            
    else:
        # Short entry logic (mirror image)
        effective_breakout = min(breakout_level, current_open)
        
        if current_low <= effective_breakout <= current_high:
            return effective_breakout * (1 - spread)
        else:
            overshoot_ratio = (effective_breakout - current_low) / atr_value
            slippage_pct = min(0.25 + 0.3 * overshoot_ratio, MAX_SLIPPAGE_PCT)
            slippage = max(atr_value * slippage_pct, effective_breakout * MIN_SLIPPAGE)
            fill_price = effective_breakout * (1 - spread) - min(slippage, effective_breakout - current_low)
            return round(fill_price, 6)

def exit_at_market_close(position_type: str, 
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
    
    if position_type == "Long":
        # Volume-weighted exit price (70% close, 30% low, adjusted by volume)
        exit_price = (current_close*0.7 + current_low*0.3) * (1 - 0.1*(1 - vol_ratio))
        
        # ATR-based protection (minimum fill improvement)
        min_fill = current_close - 0.3 * atr_value
        exit_price = max(exit_price, min_fill, SL)
        
        pnl = (exit_price - entry_price) * position_size
    
    elif position_type == "Short":
        # Volume-weighted exit price (70% close, 30% high)
        exit_price = (current_close*0.7 + current_high*0.3) * (1 + 0.1*(1 - vol_ratio))
        
        # ATR-based protection
        max_fill = current_close + 0.3 * atr_value
        exit_price = min(exit_price, max_fill, SL)
        
        pnl = (entry_price - exit_price) * position_size
    
    return exit_price, pnl

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
    
    returns = []
    
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
        positioned = False
        position = None
        SL = TP = rounded_TP = rounded_SL = None
        entry_price = None

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

            if current_time >= mid_time and not positioned:
                break

            if current_time >= end_time and positioned:
                exit_price, pnl = exit_at_market_close(
                    position_type=position,
                    entry_price=entry_price,
                    current_low=current_low,
                    current_high=current_high,
                    current_close=current_close,
                    current_volume=current_volume,
                    avg_volume=current_avg_vol,
                    atr_value=current_atr,
                    SL=SL,
                    position_size=no_of_long_shares if position == "Long" else no_of_short_shares
                )
                
                daily_pl += pnl
                positioned = False
                
                if DEBUG:
                    print(f"{current_time} - Market Close Exit | "
                        f"Position: {position} | "
                        f"Exit: {exit_price:.5f} | "
                        f"Vol Ratio: {current_volume/current_avg_vol:.2f}x | "
                        f"PnL: {pnl:.2f}", 
                        file=f)
                break

            # Long entry conditions
            if ((current_close > first_15m_high and not positioned) # original condition
                and should_trade_based_on_ema(prev_close, last_ema, last_ema_slope) # ema condition
                and should_trade_based_on_vol(current_volume, current_avg_vol) # volume condition
                ):
                ABS_SL = ATR_SL_MULTIPLIER * current_atr
                ABS_TP = ATR_TP_MULTIPLIER * current_atr
                entry_price = get_fill_price(first_15m_high, current_low, current_high, current_open, current_atr)
                no_of_long_shares = calculate_qty(Margin, ABS_SL, entry_price)
                SL = entry_price - ABS_SL
                TP = entry_price + ABS_TP
                if ABS_TP >= 0.5 and ABS_SL >= 0.5 and no_of_long_shares > 0:
                    positioned = True
                    position = "Long"
                    no_of_trades += 1
                    if DEBUG:
                        print(f"{current_date} Long entry at {current_time} @{entry_price:.2f}, qty: {no_of_long_shares}, SL: {SL:.2f}, TP: {TP:.2f}", file=f)
                else:
                    print("Rejecting trade due to small sl/tp", file=f) if DEBUG else None
                
                continue

            # Short entry conditions
            elif ((current_close < first_15m_low and not positioned) # original condition
                and should_trade_based_on_ema(prev_close, last_ema, last_ema_slope, "short") # ema condition
                and should_trade_based_on_vol(current_volume, current_avg_vol) # volume condition
                ):
                ABS_SL = ATR_SL_MULTIPLIER * current_atr
                ABS_TP = ATR_TP_MULTIPLIER * current_atr
                entry_price = get_fill_price(first_15m_low, current_low, current_high, current_open, current_atr, is_long=False)
                no_of_short_shares = calculate_qty(Margin, ABS_SL, entry_price)
                SL = entry_price + ABS_SL
                TP = entry_price - ABS_TP
                if ABS_TP >= 0.5 and ABS_SL >= 0.5 and no_of_short_shares > 0:
                    positioned = True
                    position = "Short"
                    no_of_trades += 1
                    if DEBUG:
                        print(f"{current_date} Short entry at {current_time} @{entry_price:.2f}, qty: {no_of_short_shares}, SL: {SL:.2f}, TP: {TP:.2f}", file=f)
                else:
                    print("Rejecting trade due to small sl/tp", file=f) if DEBUG else None
                
                continue

            # Exit conditions for Long
            if positioned and position == "Long":
                # Take Profit Logic
                if current_high >= TP:
                    if not ENABLED_TRAILING:
                        daily_pl += (TP - entry_price) * no_of_long_shares  # TP is <= current_high by definition
                        wins += 1
                        positioned = False
                        if DEBUG: print(f"{current_time} TP hit at {TP:.4f}")
                        break
                    
                    # Trailing Stop Logic
                    elif ENABLED_TRAILING:
                        new_sl = current_high - (ATR_TRAIL_MULTIPLIER * current_atr)
                        if new_sl > SL:  # Only tighten the SL
                            SL = new_sl
                            if DEBUG: print(f"{current_time} Trail SL updated to {SL:.4f}")
                
                # Stop Loss Logic
                if current_low <= SL:
                    daily_pl += (SL - entry_price) * no_of_long_shares  # SL is >= current_low when condition triggers
                    if ENABLED_TRAILING and (SL - entry_price) > 0:
                        wins += 1  # Only count as win if profitable
                    positioned = False
                    if DEBUG: print(f"{current_time} SL hit at {SL:.4f}")
                    break

            # Exit conditions for Short (identical cleanup)
            elif positioned and position == "Short":
                if current_low <= TP:
                    if not ENABLED_TRAILING:
                        daily_pl += (entry_price - TP) * no_of_short_shares
                        wins += 1
                        positioned = False
                        if DEBUG: print(f"{current_time} TP hit at {TP:.4f}")
                        break
                    
                    elif ENABLED_TRAILING:
                        new_sl = current_low + (ATR_TRAIL_MULTIPLIER * current_atr)
                        if new_sl < SL:  # Only tighten the SL
                            SL = new_sl
                            if DEBUG: print(f"{current_time} Trail SL updated to {SL:.4f}")
                
                if current_high >= SL:
                    daily_pl += (entry_price - SL) * no_of_short_shares
                    if ENABLED_TRAILING and (entry_price - SL) > 0:
                        wins += 1
                    positioned = False
                    if DEBUG: print(f"{current_time} SL hit at {SL:.4f}")
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


