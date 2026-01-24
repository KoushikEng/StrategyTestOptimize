"""
Debug script to understand caching behavior.
"""

import numpy as np
from strategies.Base import Base


class DebugStrategy(Base):
    def __init__(self):
        super().__init__()
        self.calculation_counts = {}
    
    def init(self):
        def counting_indicator(prices, period):
            key = f"period_{period}"
            self.calculation_counts[key] = self.calculation_counts.get(key, 0) + 1
            print(f"Calculating indicator for period {period}, call count: {self.calculation_counts[key]}")
            return np.convolve(prices, np.ones(period)/period, mode='same')
        
        closes = self.get_full_data_array('close')
        print(f"Closes array id: {id(closes)}")
        
        # Register same indicator multiple times
        print("Registering first indicator...")
        ind1 = self.I(counting_indicator, closes, 5)
        print(f"First indicator id: {id(ind1)}")
        
        print("Registering second indicator with same parameters...")
        ind2 = self.I(counting_indicator, closes, 5)
        print(f"Second indicator id: {id(ind2)}")
        
        print(f"Are they the same object? {ind1 is ind2}")
        print(f"Cache contents: {list(self._indicators.keys())}")
    
    def next(self):
        pass
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}


# Create test data
data_length = 50
symbol = "TEST"
timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
closes = np.random.uniform(100, 200, data_length).astype(np.float64)
opens = closes - 1
highs = closes + 1
lows = closes - 1
volume = np.full(data_length, 1000, dtype=np.int64)

data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)

strategy = DebugStrategy()
strategy._execute_strategy(data_tuple)