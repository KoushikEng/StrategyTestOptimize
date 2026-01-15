"""
Auto-generated strategy: KeltnerChannelStrategy
Trend following using a Keltner Channel with a 20‑period EMA and ATR multiplier of 2.
"""

from strategies.Base import Base
import numpy as np
from numba import njit
from calculate.indicators import calculate_keltner_channel

class KeltnerChannelStrategy(Base):
    """
    Trend following using a Keltner Channel with a 20‑period EMA and ATR multiplier of 2.
    """
    
    def run(self, data, **kwargs):
        symbol, dates, times, opens, highs, lows, closes, volume = data
        
        n = len(closes)
        returns = np.zeros(n)
        
        # Calculate indicators
        kc = calculate_keltner_channel(highs, lows, closes, period=20, multiplier=2)
        
        # Trading logic
        in_position = False
        entry_price = 0.0
        
        # Determine start index (need enough data for indicators)
        start_idx = 50  # Safe default, adjust based on longest indicator period
        
        for i in range(start_idx, n):
            # Entry
            if not in_position:
                try:
                    if (close[i] > kc.upper[i] and (kc.upper[i] - kc.lower[i]) > (kc.upper[i-1] - kc.lower[i-1]) and close[i] <= kc.middle[i]) and (close[i] < kc.lower[i] and (kc.upper[i] - kc.lower[i]) > (kc.upper[i-1] - kc.lower[i-1]) and close[i] >= kc.middle[i]):
                        in_position = True
                        entry_price = closes[i]
                except:
                    pass
            
            # Exit
            elif in_position:
                try:
                    if (close[i] < kc.lower[i]) or (close[i] > kc.upper[i]):
                        in_position = False
                        exit_price = closes[i]
                        returns[i] = (exit_price - entry_price) / entry_price
                except:
                    pass
        
        return returns
    
    def validate_params(self, **kwargs) -> bool:
        # Auto-generated: no custom validation
        return True
    
    @staticmethod
    def get_optimization_params():
        return {
            "period": (10, 30),
            "atr_period": (10, 30),
            "multiplier": (1, 3),
        }
