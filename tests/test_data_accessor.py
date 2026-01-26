"""
Property-based tests for DataAccessor data type preservation and interface.
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from strategies.Base import DataAccessor, StrategyContext
from Utilities import DataTuple


class TestDataAccessorProperties:
    """Property-based tests for DataAccessor."""
    
    @given(
        data_length=st.integers(min_value=10, max_value=100),
        current_index=st.integers(min_value=0, max_value=99)
    )
    def test_data_type_preservation_property(self, data_length, current_index):
        """
        **Feature: strategy-base-enhancement, Property 7: Data Type Preservation**
        
        For any input DataTuple, the system should preserve all data types 
        (np.float64 for prices, np.int64 for timestamps and volume) throughout processing.
        
        **Validates: Requirements 7.5**
        """
        assume(current_index < data_length)
        
        # Create test data with correct types
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        opens = np.random.uniform(100, 200, data_length).astype(np.float64)
        highs = opens + np.random.uniform(0, 10, data_length).astype(np.float64)
        lows = opens - np.random.uniform(0, 10, data_length).astype(np.float64)
        closes = np.random.uniform(lows, highs).astype(np.float64)
        volume = np.random.randint(1000, 10000, data_length, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        context = StrategyContext()
        context.set_data_length(data_length)
        context.update_index(current_index)
        
        accessor = DataAccessor(data_tuple, context)
        
        # Property: Original data types should be preserved in internal storage
        assert accessor._original_timestamps.dtype == np.int64, f"Timestamps should be int64, got {accessor._original_timestamps.dtype}"
        assert accessor._original_volume.dtype == np.int64, f"Volume should be int64, got {accessor._original_volume.dtype}"
        
        # Property: Price data should be accessible as float64
        assert isinstance(accessor.Open[-1], float), "Open price should be accessible as float"
        assert isinstance(accessor.High[-1], float), "High price should be accessible as float"
        assert isinstance(accessor.Low[-1], float), "Low price should be accessible as float"
        assert isinstance(accessor.Close[-1], float), "Close price should be accessible as float"
        
        # Property: Current bar data should return correct types
        current_bar = accessor.get_current_bar_data()
        assert isinstance(current_bar['timestamp'], int), "Timestamp should be returned as int"
        assert isinstance(current_bar['open'], float), "Open should be returned as float"
        assert isinstance(current_bar['high'], float), "High should be returned as float"
        assert isinstance(current_bar['low'], float), "Low should be returned as float"
        assert isinstance(current_bar['close'], float), "Close should be returned as float"
        assert isinstance(current_bar['volume'], int), "Volume should be returned as int"
        
        # Property: Values should match original data
        assert current_bar['timestamp'] == timestamps[current_index]
        assert current_bar['open'] == opens[current_index]
        assert current_bar['high'] == highs[current_index]
        assert current_bar['low'] == lows[current_index]
        assert current_bar['close'] == closes[current_index]
        assert current_bar['volume'] == volume[current_index]
    
    @given(
        data_length=st.integers(min_value=5, max_value=50),
        indices=st.lists(st.integers(min_value=0, max_value=49), min_size=1, max_size=10)
    )
    def test_data_accessor_interface_property(self, data_length, indices):
        """
        Property test for DataAccessor interface consistency and OHLCV access.
        """
        valid_indices = [idx for idx in indices if idx < data_length]
        assume(len(valid_indices) > 0)
        
        # Create test data
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        opens = np.full(data_length, 100.0, dtype=np.float64)
        highs = np.full(data_length, 110.0, dtype=np.float64)
        lows = np.full(data_length, 90.0, dtype=np.float64)
        closes = np.full(data_length, 105.0, dtype=np.float64)
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        context = StrategyContext()
        context.set_data_length(data_length)
        accessor = DataAccessor(data_tuple, context)
        
        for idx in valid_indices:
            context.update_index(idx)
            
            # Property: All OHLCV data should be accessible
            assert accessor.Open[-1] == 100.0, "Open should be accessible"
            assert accessor.High[-1] == 110.0, "High should be accessible"
            assert accessor.Low[-1] == 90.0, "Low should be accessible"
            assert accessor.Close[-1] == 105.0, "Close should be accessible"
            assert accessor.Volume[-1] == 1000.0, "Volume should be accessible as float"
            
            # Property: Symbol should be preserved
            assert accessor.symbol == symbol, "Symbol should be preserved"
            
            # Property: Array-like access should work for all series
            assert accessor.Open[idx] == 100.0, f"Open[{idx}] should work"
            assert accessor.High[idx] == 110.0, f"High[{idx}] should work"
            assert accessor.Low[idx] == 90.0, f"Low[{idx}] should work"
            assert accessor.Close[idx] == 105.0, f"Close[{idx}] should work"
            assert accessor.Volume[idx] == 1000.0, f"Volume[{idx}] should work"


class TestDataAccessorErrorConditions:
    """Unit tests for DataAccessor error conditions and edge cases."""
    
    def test_invalid_data_tuple_format(self):
        """Test that invalid DataTuple formats are rejected."""
        context = StrategyContext()
        context.set_data_length(1)
        
        # Test wrong number of elements
        with pytest.raises(ValueError, match="Data must be a 7-element DataTuple"):
            DataAccessor((1, 2, 3), context)
        
        with pytest.raises(ValueError, match="Data must be a 7-element DataTuple"):
            DataAccessor((1, 2, 3, 4, 5, 6, 7, 8), context)
        
        # Test non-tuple input
        with pytest.raises(ValueError, match="Data must be a 7-element DataTuple"):
            DataAccessor([1, 2, 3, 4, 5, 6, 7], context)
    
    def test_mismatched_array_lengths(self):
        """Test that mismatched array lengths are rejected."""
        context = StrategyContext()
        context.set_data_length(3)
        
        symbol = "TEST"
        timestamps = np.array([1, 2, 3], dtype=np.int64)
        opens = np.array([100.0, 101.0], dtype=np.float64)  # Wrong length
        highs = np.array([110.0, 111.0, 112.0], dtype=np.float64)
        lows = np.array([90.0, 91.0, 92.0], dtype=np.float64)
        closes = np.array([105.0, 106.0, 107.0], dtype=np.float64)
        volume = np.array([1000, 1001, 1002], dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        with pytest.raises(ValueError, match="All data arrays must have the same length"):
            DataAccessor(data_tuple, context)
    
    def test_data_type_conversion(self):
        """Test that data types are correctly converted."""
        context = StrategyContext()
        context.set_data_length(3)
        context.update_index(1)
        
        symbol = "TEST"
        # Provide data in wrong types to test conversion
        timestamps = [1600000000, 1600000001, 1600000002]  # List instead of array
        opens = [100, 101, 102]  # Integers instead of floats
        highs = [110, 111, 112]
        lows = [90, 91, 92]
        closes = [105, 106, 107]
        volume = [1000.0, 1001.0, 1002.0]  # Floats instead of integers
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        accessor = DataAccessor(data_tuple, context)
        
        # Should convert and work correctly
        assert accessor._original_timestamps.dtype == np.int64
        assert accessor._original_volume.dtype == np.int64
        assert accessor.Open[-1] == 101.0
        assert accessor.Volume[-1] == 1001.0
    
    def test_datatuple_compatibility(self):
        """Test compatibility with actual DataTuple format from Utilities."""
        context = StrategyContext()
        context.set_data_length(5)
        context.update_index(2)
        
        # Create data in the exact format returned by read_from_csv
        symbol = "AAPL"
        timestamps = np.array([1600000000, 1600000060, 1600000120, 1600000180, 1600000240], dtype=np.int64)
        opens = np.array([150.0, 151.0, 152.0, 153.0, 154.0], dtype=np.float64)
        highs = np.array([155.0, 156.0, 157.0, 158.0, 159.0], dtype=np.float64)
        lows = np.array([149.0, 150.0, 151.0, 152.0, 153.0], dtype=np.float64)
        closes = np.array([154.0, 155.0, 156.0, 157.0, 158.0], dtype=np.float64)
        volume = np.array([10000, 11000, 12000, 13000, 14000], dtype=np.int64)
        
        data_tuple: DataTuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        accessor = DataAccessor(data_tuple, context)
        
        # Test that all data is accessible and correct
        assert accessor.symbol == "AAPL"
        assert accessor.Open[-1] == 152.0  # Current bar (index 2)
        assert accessor.High[-1] == 157.0
        assert accessor.Low[-1] == 151.0
        assert accessor.Close[-1] == 156.0
        assert accessor.Volume[-1] == 12000.0
        
        # Test current bar data
        current_bar = accessor.get_current_bar_data()
        assert current_bar['timestamp'] == 1600000120
        assert current_bar['open'] == 152.0
        assert current_bar['high'] == 157.0
        assert current_bar['low'] == 151.0
        assert current_bar['close'] == 156.0
        assert current_bar['volume'] == 12000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])