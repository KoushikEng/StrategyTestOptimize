from strategies.Base import Base
import numpy as np
import pandas as pd
from numba import njit
from Utilities import DataTuple

@njit
def fast_numba_strategy(closes, fast_ma_period, slow_ma_period):
    n = len(closes)
    
    # Calculate MAs (Simple implementation for speed)
    fast_ma = np.full(n, np.nan)
    slow_ma = np.full(n, np.nan)
    
    running_sum_fast = 0.0
    running_sum_slow = 0.0
    
    for i in range(n):
        running_sum_fast += closes[i]
        running_sum_slow += closes[i]
        
        if i >= fast_ma_period:
            running_sum_fast -= closes[i - fast_ma_period]
            fast_ma[i] = running_sum_fast / fast_ma_period
            
        if i >= slow_ma_period:
            running_sum_slow -= closes[i - slow_ma_period]
            slow_ma[i] = running_sum_slow / slow_ma_period

    # Generate signals
    entries = np.zeros(n)
    exits = np.zeros(n)
    in_position = False
    
    # 0: long, 1: none
    
    returns = np.zeros(n)
    
    # Very simple vectorized backtest logic within the loop
    entry_price = 0.0
    
    # We need at least slow_ma_period to have values
    start_idx = slow_ma_period
    
    for i in range(start_idx, n):
        # Cross Over: Fast crosses above Slow -> Buy
        if not in_position and fast_ma[i] > slow_ma[i] and fast_ma[i-1] <= slow_ma[i-1]:
            in_position = True
            entry_price = closes[i]
            entries[i] = 1
            
        # Cross Under: Fast crosses below Slow -> Sell
        elif in_position and fast_ma[i] < slow_ma[i] and fast_ma[i-1] >= slow_ma[i-1]:
            in_position = False
            exit_price = closes[i]
            exits[i] = 1
            ret = (exit_price - entry_price) / entry_price
            returns[i] = ret
            
    return returns, entries, exits

class SimpleMACross(Base):
    
    def run(self, data: DataTuple, fast_ma=50, slow_ma=200, **kwargs):
        symbol, dates, times, opens, highs, lows, closes, volume = data
        
        # Ensure parameters are integers
        fast_ma = int(fast_ma)
        slow_ma = int(slow_ma)
        
        returns, _, _ = fast_numba_strategy(closes, fast_ma, slow_ma)
        
        return returns
    
    def validate_params(self, fast_ma=50, slow_ma=200, **kwargs) -> bool:
        return slow_ma > fast_ma

    @staticmethod
    def get_optimization_params():
        return {
            "fast_ma": (5, 200),
            "slow_ma": (50, 500)
        }
