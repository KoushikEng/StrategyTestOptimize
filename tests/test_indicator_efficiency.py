"""
Property-based tests for indicator calculation efficiency.
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from strategies.Base import Base
from unittest.mock import Mock, call
from Utilities import DataTuple


class IndicatorEfficiencyTestStrategy(Base):
    """Test strategy for indicator efficiency testing."""
    
    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.indicator_func = None
    
    def init(self):
        """Initialize indicators with call counting."""
        def counting_sma(prices, period):
            self.call_count += 1
            return np.convolve(prices, np.ones(period)/period, mode='same')
        
        self.indicator_func = counting_sma
        closes = self.get_full_data_array('close')
        
        # Register same indicator multiple times
        self.sma1 = self.I(counting_sma, closes, 10)
        self.sma2 = self.I(counting_sma, closes, 10)  # Same parameters - should be cached
        self.sma3 = self.I(counting_sma, closes, 10)  # Same parameters - should be cached
        self.sma4 = self.I(counting_sma, closes, 20)  # Different parameters - should calculate
    
    def next(self):
        """Process current bar."""
        pass
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}


def counting_indicator_func(prices, period, counter_dict):
    """Global indicator function for consistent caching."""
    key = f"period_{period}"
    counter_dict[key] = counter_dict.get(key, 0) + 1
    return np.convolve(prices, np.ones(period)/period, mode='same')


class TestIndicatorCalculationEfficiency:
    """Property-based tests for indicator calculation efficiency."""
    
    def test_indicator_calculation_efficiency_property_simple(self):
        """
        **Feature: strategy-base-enhancement, Property 2: Indicator Calculation Efficiency**
        
        For any registered indicator, the calculation function should be called exactly once 
        during registration, and subsequent accesses should return cached values without recalculation.
        
        **Validates: Requirements 2.2, 2.4, 2.5**
        """
        # Create test data
        data_length = 100
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.arange(100, 200, dtype=np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        # Use a global counter to track function calls
        call_count = {'count': 0}
        
        def counting_sma(prices, period):
            call_count['count'] += 1
            return np.convolve(prices, np.ones(period)/period, mode='same')
        
        class EfficiencyTestStrategy(Base):
            def init(self):
                closes = self.get_full_data_array('close')
                
                # Register same indicator multiple times - should be cached
                self.sma1 = self.I(counting_sma, closes, 10)
                self.sma2 = self.I(counting_sma, closes, 10)  # Same params - should be cached
                self.sma3 = self.I(counting_sma, closes, 10)  # Same params - should be cached
                self.sma4 = self.I(counting_sma, closes, 20)  # Different params - should calculate
                self.sma5 = self.I(counting_sma, closes, 20)  # Same as sma4 - should be cached
            
            def next(self):
                pass
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = EfficiencyTestStrategy()
        strategy._execute_strategy(data_tuple)
        
        # Property: Function should be called exactly twice (once for period 10, once for period 20)
        assert call_count['count'] == 2, f"Expected 2 calls, got {call_count['count']}"
        
        # Property: Same parameters should return same cached object
        assert strategy.sma1 is strategy.sma2, "Same parameters should return cached object"
        assert strategy.sma1 is strategy.sma3, "Same parameters should return cached object"
        assert strategy.sma4 is strategy.sma5, "Same parameters should return cached object"
        assert strategy.sma1 is not strategy.sma4, "Different parameters should return different objects"
    
    def test_indicator_caching_with_mock(self):
        """Test indicator caching using mock to verify call counts."""
        # Create test data
        data_length = 50
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.arange(100, 150, dtype=np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        # Create mock indicator function
        mock_indicator = Mock(return_value=np.ones(data_length))
        mock_indicator.__name__ = 'mock_sma'
        
        class MockTestStrategy(Base):
            def init(self):
                closes = self.get_full_data_array('close')
                # Register same indicator multiple times
                self.ind1 = self.I(mock_indicator, closes, 10)
                self.ind2 = self.I(mock_indicator, closes, 10)  # Same params - should be cached
                self.ind3 = self.I(mock_indicator, closes, 20)  # Different params - should calculate
                self.ind4 = self.I(mock_indicator, closes, 10)  # Same as first - should be cached
            
            def next(self):
                pass
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = MockTestStrategy()
        strategy._execute_strategy(data_tuple)
        
        # Property: Mock should be called exactly twice (once for period 10, once for period 20)
        assert mock_indicator.call_count == 2, f"Expected 2 calls, got {mock_indicator.call_count}"
        
        # Property: Cached indicators should return same object
        assert strategy.ind1 is strategy.ind2, "Same parameters should return cached object"
        assert strategy.ind1 is strategy.ind4, "Same parameters should return cached object"
        assert strategy.ind1 is not strategy.ind3, "Different parameters should return different object"
    
    def test_indicator_access_efficiency(self):
        """Test that indicator access doesn't trigger recalculation."""
        data_length = 30
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.arange(100, 130, dtype=np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        strategy = IndicatorEfficiencyTestStrategy()
        strategy._execute_strategy(data_tuple)
        
        # Property: Indicator function should be called exactly twice (period 10 and period 20)
        assert strategy.call_count == 2, f"Expected 2 calls, got {strategy.call_count}"
        
        # Reset call count and access indicators multiple times during execution
        initial_call_count = strategy.call_count
        
        # Simulate accessing indicators during strategy execution
        for i in range(10, data_length):
            strategy._context.update_index(i)
            # Access indicators multiple times - should not trigger recalculation
            _ = strategy.sma1[-1]
            _ = strategy.sma2[-1]
            _ = strategy.sma3[-1]
            _ = strategy.sma4[-1]
            _ = strategy.sma1.values
            _ = strategy.sma2.values
        
        # Property: No additional calculations should have occurred
        assert strategy.call_count == initial_call_count, f"Indicator access should not trigger recalculation, but call count increased from {initial_call_count} to {strategy.call_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])