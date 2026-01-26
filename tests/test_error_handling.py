"""
Property-based tests for error handling robustness.
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from strategies.Base import Base
from Utilities import DataTuple


class TestErrorHandlingRobustness:
    """Property-based tests for error handling robustness."""
    
    @given(
        invalid_indices=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1, max_size=10),
        data_length=st.integers(min_value=10, max_value=50)
    )
    def test_error_handling_robustness_property(self, invalid_indices, data_length):
        """
        **Feature: strategy-base-enhancement, Property 9: Error Handling Robustness**
        
        For any invalid input or operation (invalid indices, missing methods, invalid parameters), 
        the system should raise appropriate, descriptive errors rather than failing silently 
        or producing incorrect results.
        
        **Validates: Requirements 9.2, 9.3**
        """
        # Create test data
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.random.uniform(100, 200, data_length).astype(np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        class ErrorTestStrategy(Base):
            def init(self):
                self.indicator = self.I(lambda x: np.ones(len(x)), self.get_full_data_array('close'))
            
            def next(self):
                pass
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = ErrorTestStrategy()
        strategy._execute_strategy(data_tuple)
        
        # Test invalid index access on indicators
        for invalid_idx in invalid_indices:
            # Filter out valid indices (including negative indices that are valid)
            current_idx = data_length // 2
            strategy._context.update_index(current_idx)
            
            # Valid negative indices: -1 to -(current_idx + 1)
            # Valid positive indices: 0 to current_idx
            if (-current_idx - 1 <= invalid_idx <= current_idx):
                continue
            
            # Property: Invalid indices should raise IndexError with descriptive message
            with pytest.raises(IndexError) as exc_info:
                _ = strategy.indicator[invalid_idx]
            
            # Property: Error message should be descriptive
            error_msg = str(exc_info.value)
            assert len(error_msg) > 0, "Error message should not be empty"
            assert "Index" in error_msg or "index" in error_msg, f"Error message should mention index: {error_msg}"
    
    def test_invalid_data_tuple_errors(self):
        """Test error handling for invalid DataTuple formats."""
        
        class TestStrategy(Base):
            def init(self):
                pass
            
            def next(self):
                pass
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = TestStrategy()
        
        # Property: Invalid tuple length should raise descriptive error
        with pytest.raises(ValueError, match="Data must be a 7-element DataTuple"):
            strategy._execute_strategy((1, 2, 3))  # Too few elements
        
        with pytest.raises(ValueError, match="Data must be a 7-element DataTuple"):
            strategy._execute_strategy((1, 2, 3, 4, 5, 6, 7, 8))  # Too many elements
        
        # Property: Non-tuple input should raise descriptive error
        with pytest.raises(ValueError, match="Data must be a 7-element DataTuple"):
            strategy._execute_strategy([1, 2, 3, 4, 5, 6, 7])  # List instead of tuple
    
    def test_indicator_registration_errors(self):
        """Test error handling for indicator registration failures."""
        
        # Create valid test data
        data_length = 20
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.arange(100, 120, dtype=np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        class IndicatorErrorStrategy(Base):
            def __init__(self):
                super().__init__()
                self.test_phase = None
            
            def init(self):
                closes = self.get_full_data_array('close')
                
                if self.test_phase == "non_callable":
                    # Property: Non-callable should raise TypeError
                    with pytest.raises(TypeError, match="Indicator function must be callable"):
                        self.I("not_a_function", closes)
                
                elif self.test_phase == "wrong_length":
                    # Property: Wrong length indicator should raise ValueError
                    def wrong_length_indicator(prices):
                        return np.ones(5)  # Wrong length
                    
                    with pytest.raises(RuntimeError, match="Failed to register indicator"):
                        self.I(wrong_length_indicator, closes)
                
                elif self.test_phase == "invalid_return":
                    # Property: Non-array return should be handled
                    def invalid_return_indicator(prices):
                        return "not an array"
                    
                    # This should raise an error because string can't be converted to numeric array
                    with pytest.raises(RuntimeError, match="Failed to register indicator"):
                        self.I(invalid_return_indicator, closes)
            
            def next(self):
                pass
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        # Test non-callable indicator
        strategy1 = IndicatorErrorStrategy()
        strategy1.test_phase = "non_callable"
        strategy1._execute_strategy(data_tuple)
        
        # Test wrong length indicator
        strategy2 = IndicatorErrorStrategy()
        strategy2.test_phase = "wrong_length"
        strategy2._execute_strategy(data_tuple)
        
        # Test invalid return type handling
        strategy3 = IndicatorErrorStrategy()
        strategy3.test_phase = "invalid_return"
        strategy3._execute_strategy(data_tuple)
    
    def test_position_management_errors(self):
        """Test error handling for position management operations."""
        
        # Create test data
        data_length = 10
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.arange(100, 110, dtype=np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        class PositionErrorStrategy(Base):
            def __init__(self):
                super().__init__()
                self.test_phase = None
            
            def init(self):
                pass
            
            def next(self):
                current_idx = self._context.get_current_index()
                
                if self.test_phase == "buy_when_in_position" and current_idx == 2:
                    # First buy should work
                    self.buy(1.0)
                elif self.test_phase == "buy_when_in_position" and current_idx == 3:
                    # Second buy should fail
                    with pytest.raises(ValueError, match="Already in position"):
                        self.buy(1.0)
                
                elif self.test_phase == "sell_when_not_in_position" and current_idx == 2:
                    # Sell without position should fail
                    with pytest.raises(ValueError, match="No position to close"):
                        self.sell()
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        # Test buy when already in position
        strategy1 = PositionErrorStrategy()
        strategy1.test_phase = "buy_when_in_position"
        strategy1._execute_strategy(data_tuple)
        
        # Test sell when not in position
        strategy2 = PositionErrorStrategy()
        strategy2.test_phase = "sell_when_not_in_position"
        strategy2._execute_strategy(data_tuple)
    
    def test_context_boundary_errors(self):
        """Test error handling for context boundary violations."""
        
        # Create test data
        data_length = 10
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.arange(100, 110, dtype=np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        class ContextErrorStrategy(Base):
            def init(self):
                self.indicator = self.I(lambda x: np.arange(len(x)), self.get_full_data_array('close'))
            
            def next(self):
                current_idx = self._context.get_current_index()
                
                if current_idx == 5:  # Test at middle of data
                    # Property: Accessing future data should raise IndexError
                    with pytest.raises(IndexError, match="would access future data"):
                        _ = self.indicator[current_idx + 1]
                    
                    # Property: Accessing too far back should raise IndexError
                    with pytest.raises(IndexError, match="would access data before start"):
                        _ = self.indicator[-(current_idx + 2)]
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = ContextErrorStrategy()
        strategy._execute_strategy(data_tuple)
    
    def test_data_accessor_errors(self):
        """Test error handling in DataAccessor."""
        from strategies.Base import DataAccessor, StrategyContext
        
        context = StrategyContext()
        context.set_data_length(5)
        
        # Property: Mismatched array lengths should raise ValueError
        symbol = "TEST"
        timestamps = np.array([1, 2, 3], dtype=np.int64)  # Length 3
        opens = np.array([100, 101], dtype=np.float64)    # Length 2 - mismatch
        highs = np.array([110, 111, 112], dtype=np.float64)
        lows = np.array([90, 91, 92], dtype=np.float64)
        closes = np.array([105, 106, 107], dtype=np.float64)
        volume = np.array([1000, 1001, 1002], dtype=np.int64)
        
        invalid_data = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        with pytest.raises(ValueError, match="All data arrays must have the same length"):
            DataAccessor(invalid_data, context)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])