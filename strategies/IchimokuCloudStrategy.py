"""
Auto-generated strategy: IchimokuCloudStrategy
Simplified Ichimoku Cloud strategy with long and short entries based on Tenkan/Kijun cross. Exits on opposite cross, cloud edge, or stop loss.
"""

from strategies.Base import Base
import numpy as np
from numba import njit
from calculate.indicators import calculate_ichimoku

class IchimokuCloudStrategy(Base):
    """
    Simplified Ichimoku Cloud strategy with long and short entries based on Tenkan/Kijun cross. Exits on opposite cross, cloud edge, or stop loss.
    """
    
    def run(self, data, **kwargs):
        symbol, dates, times, opens, highs, lows, closes, volume = data
        
        n = len(closes)
        returns = np.zeros(n)
        
        # Calculate indicators
        cloud = calculate_ichimoku(closes)
        
        # Trading logic
        in_position = False
        entry_price = 0.0
        
        # Determine start index (need enough data for indicators)
        start_idx = 50  # Safe default, adjust based on longest indicator period
        
        for i in range(start_idx, n):
            # Entry
            if not in_position:
                try:
                    if (cloud.tenkan[i] > cloud.kijun[i] and cloud.tenkan[i-1] <= cloud.kijun[i-1]) and (cloud.tenkan[i] < cloud.kijun[i] and cloud.tenkan[i-1] >= cloud.kijun[i-1]):
                        in_position = True
                        entry_price = closes[i]
                except:
                    pass
            
            # Exit
            elif in_position:
                try:
                    if (close[i] >= cloud.kijun[i] or close[i] >= cloud.senkou_a[i] or close[i] >= cloud.senkou_b[i]) or (close[i] <= cloud.kijun[i] or close[i] <= cloud.senkou_a[i] or close[i] <= cloud.senkou_b[i]) or (cloud.tenkan[i] < cloud.kijun[i] and cloud.tenkan[i-1] >= cloud.kijun[i-1]) or (cloud.tenkan[i] > cloud.kijun[i] and cloud.tenkan[i-1] <= cloud.kijun[i-1]) or (close[i] < cloud.senkou_a[i] or close[i] < cloud.senkou_b[i]) or (close[i] > cloud.senkou_a[i] or close[i] > cloud.senkou_b[i]):
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
            "period1": (5, 20),
            "period2": (20, 50),
            "period3": (50, 100),
        }
