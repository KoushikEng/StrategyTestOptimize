"""
Property-based tests for IndicatorWrapper array-like access and look-ahead prevention.
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from strategies.Base import IndicatorWrapper, StrategyContext


class TestIndicatorWrapperProperties:
    """Property-based tests for IndicatorWrapper."""
    
    @given(
        data_length=st.integers(min_value=10, max_value=1000),
        current_indices=st.lists(st.integers(min_value=0, max_value=999), min_size=1, max_size=50),
        negative_indices=st.lists(st.integers(min_value=-10, max_value=-1), min_size=1, max_size=10),
        positive_indices=st.lists(st.integers(min_value=0, max_value=999), min_size=1, max_size=10)
    )
    def test_indicator_array_like_access_property(self, data_length, current_indices, negative_indices, positive_indices):
        """
        **Feature: strategy-base-enhancement, Property 5: Indicator Array-like Access**
        
        For any indicator wrapper and valid index, negative indexing should work like Python arrays 
        (with -1 being current bar, -2 being previous bar), and positive indexing should work within 
        the current bounds.
        
        **Validates: Requirements 5.1, 5.2, 5.4, 5.5**
        """
        # Filter indices to be within bounds
        valid_current_indices = [idx for idx in current_indices if idx < data_length]
        assume(len(valid_current_indices) > 0)
        
        # Create test data
        values = np.random.randn(data_length).astype(np.float64)
        context = StrategyContext()
        context.set_data_length(data_length)
        wrapper = IndicatorWrapper(values, context)
        
        for current_idx in valid_current_indices:
            context.update_index(current_idx)
            
            # Property: Negative indexing should work like Python arrays
            for neg_idx in negative_indices:
                if current_idx + neg_idx + 1 >= 0:  # Valid negative index
                    expected_actual_idx = current_idx + neg_idx + 1
                    result = wrapper[neg_idx]
                    expected = values[expected_actual_idx]
                    assert result == expected, f"Negative index {neg_idx} at current {current_idx} failed"
            
            # Property: Positive indexing should work within current bounds
            for pos_idx in positive_indices:
                if pos_idx <= current_idx:  # Valid positive index
                    result = wrapper[pos_idx]
                    expected = values[pos_idx]
                    assert result == expected, f"Positive index {pos_idx} at current {current_idx} failed"
            
            # Property: -1 should always return current bar value
            if current_idx >= 0:
                assert wrapper[-1] == values[current_idx], "Index -1 should return current bar"
            
            # Property: -2 should return previous bar value (if exists)
            if current_idx >= 1:
                assert wrapper[-2] == values[current_idx - 1], "Index -2 should return previous bar"
    
    @given(
        data_length=st.integers(min_value=5, max_value=100),
        current_index=st.integers(min_value=0, max_value=99)
    )
    def test_look_ahead_prevention_property(self, data_length, current_index):
        """
        **Feature: strategy-base-enhancement, Property 3: Look-ahead Prevention**
        
        For any data access during strategy execution, the system should never allow access 
        to data beyond the current bar index, ensuring no future information influences 
        current decisions.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.5**
        """
        assume(current_index < data_length)
        
        values = np.random.randn(data_length).astype(np.float64)
        context = StrategyContext()
        context.set_data_length(data_length)
        context.update_index(current_index)
        wrapper = IndicatorWrapper(values, context)
        
        # Property: Should prevent access to future data via positive indexing
        for future_idx in range(current_index + 1, min(data_length, current_index + 10)):
            with pytest.raises(IndexError, match="would access future data"):
                _ = wrapper[future_idx]
        
        # Property: Should prevent access to future data via negative indexing
        # Negative indices that would go beyond current index should fail
        invalid_neg_idx = -(current_index + 2)  # This would access before start
        if invalid_neg_idx < -current_index - 1:
            with pytest.raises(IndexError):
                _ = wrapper[invalid_neg_idx]
        
        # Property: Values property should only return data up to current index
        sliced_values = wrapper.values
        expected_length = current_index + 1
        assert len(sliced_values) == expected_length, f"Values length should be {expected_length}, got {len(sliced_values)}"
        
        # Property: Sliced values should match original values up to current index
        np.testing.assert_array_equal(sliced_values, values[:current_index + 1])
    
    @given(
        data_length=st.integers(min_value=1, max_value=100),
        current_index=st.integers(min_value=0, max_value=99)
    )
    def test_indicator_slicing_consistency_property(self, data_length, current_index):
        """
        **Feature: strategy-base-enhancement, Property 10: Indicator Slicing Consistency**
        
        For any indicator wrapper at any execution point, the sliced data should contain 
        exactly the values from index 0 to the current index, maintaining temporal consistency.
        
        **Validates: Requirements 2.3**
        """
        assume(current_index < data_length)
        
        values = np.arange(data_length, dtype=np.float64)  # Use sequential values for easy verification
        context = StrategyContext()
        context.set_data_length(data_length)
        context.update_index(current_index)
        wrapper = IndicatorWrapper(values, context)
        
        # Property: Sliced data should contain exactly values from 0 to current_index
        sliced = wrapper.values
        expected = values[:current_index + 1]
        
        assert len(sliced) == len(expected), f"Length mismatch: got {len(sliced)}, expected {len(expected)}"
        np.testing.assert_array_equal(sliced, expected, "Sliced values don't match expected range")
        
        # Property: Length should match current accessible range
        assert len(wrapper) == current_index + 1, f"Wrapper length should be {current_index + 1}, got {len(wrapper)}"
        
        # Property: All accessible indices should return correct values
        for i in range(current_index + 1):
            assert wrapper[i] == values[i], f"Index {i} returned wrong value"


class TestIndicatorWrapperEdgeCases:
    """Unit tests for IndicatorWrapper edge cases and error conditions."""
    
    def test_empty_array_rejection(self):
        """Test that empty arrays are rejected."""
        context = StrategyContext()
        context.set_data_length(1)
        
        with pytest.raises(ValueError, match="Values array cannot be empty"):
            IndicatorWrapper(np.array([]), context)
    
    def test_non_array_rejection(self):
        """Test that non-numpy arrays are rejected."""
        context = StrategyContext()
        context.set_data_length(1)
        
        with pytest.raises(TypeError, match="Values must be numpy array"):
            IndicatorWrapper([1, 2, 3], context)
    
    def test_non_integer_index_rejection(self):
        """Test that non-integer indices are rejected."""
        values = np.array([1.0, 2.0, 3.0])
        context = StrategyContext()
        context.set_data_length(3)
        context.update_index(1)
        wrapper = IndicatorWrapper(values, context)
        
        with pytest.raises(TypeError, match="Index must be integer"):
            _ = wrapper[1.5]
        
        with pytest.raises(TypeError, match="Index must be integer"):
            _ = wrapper["invalid"]
    
    def test_boundary_conditions(self):
        """Test boundary conditions for indexing."""
        values = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        context = StrategyContext()
        context.set_data_length(5)
        
        # Test at index 0 (first bar)
        context.update_index(0)
        wrapper = IndicatorWrapper(values, context)
        
        assert wrapper[-1] == 10.0  # Current bar
        assert wrapper[0] == 10.0   # First bar
        
        # Should not be able to access previous bars when at index 0
        with pytest.raises(IndexError):
            _ = wrapper[-2]
        
        # Test at last index
        context.update_index(4)
        assert wrapper[-1] == 50.0  # Current bar
        assert wrapper[4] == 50.0   # Last bar
        assert wrapper[-5] == 10.0  # First bar via negative indexing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])