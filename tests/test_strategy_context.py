"""
Property-based tests for StrategyContext state management.
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from strategies.Base import StrategyContext


class TestStrategyContextProperties:
    """Property-based tests for StrategyContext."""
    
    @given(
        data_length=st.integers(min_value=1, max_value=10000),
        indices=st.lists(st.integers(min_value=0, max_value=9999), min_size=1, max_size=100)
    )
    def test_context_state_management_property(self, data_length, indices):
        """
        **Feature: strategy-base-enhancement, Property 4: Context State Management**
        
        For any strategy execution, the Strategy_Context should maintain the correct 
        current bar index throughout execution, updating it sequentially for each processed bar.
        
        **Validates: Requirements 3.4, 8.2**
        """
        # Filter indices to be within bounds
        valid_indices = [idx for idx in indices if idx < data_length]
        assume(len(valid_indices) > 0)
        
        context = StrategyContext()
        context.set_data_length(data_length)
        
        # Property: Context should correctly track and update current index
        for idx in valid_indices:
            context.update_index(idx)
            assert context.get_current_index() == idx, f"Expected index {idx}, got {context.get_current_index()}"
        
        # Property: Context should maintain data length correctly
        assert context._data_length == data_length
        
        # Property: Context should reject invalid indices
        with pytest.raises(IndexError):
            context.update_index(data_length)  # Out of bounds
        
        with pytest.raises(IndexError):
            context.update_index(-1)  # Negative index
    
    @given(
        data_lengths=st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=10)
    )
    def test_data_length_management_property(self, data_lengths):
        """
        Property test for data length management and index reset behavior.
        """
        context = StrategyContext()
        
        for data_length in data_lengths:
            context.set_data_length(data_length)
            
            # Property: Data length should be set correctly
            assert context._data_length == data_length
            
            # Property: Index should reset to 0 when setting new data length
            assert context.get_current_index() == 0
            
            # Property: Should be able to set index to any valid value
            if data_length > 1:
                test_idx = data_length - 1
                context.update_index(test_idx)
                assert context.get_current_index() == test_idx
    
    def test_invalid_data_length_property(self):
        """Test that invalid data lengths are rejected."""
        context = StrategyContext()
        
        # Property: Should reject zero or negative data lengths
        with pytest.raises(ValueError):
            context.set_data_length(0)
        
        with pytest.raises(ValueError):
            context.set_data_length(-1)
        
        with pytest.raises(ValueError):
            context.set_data_length(-100)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])