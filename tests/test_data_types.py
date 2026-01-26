"""
Test for data type consistency in the processing pipeline.
"""

import os
import tempfile
import numpy as np
from Utilities import process_symbol_data, read_from_csv

def test_data_type_consistency():
    """
    Property 3: Data type consistency
    **Validates: Requirements 1.3, 1.4**
    
    For any data processing operation, all timestamp arrays should be np.int64 type 
    and all price/volume arrays should be numba-compatible types (np.int64, np.float64).
    """
    # Feature: numba-optimized-datetime, Property 3: Data type consistency
    
    print("Testing data type consistency...")
    
    # Create test data with various numeric types
    test_data = [
        [1704096900, 100.0, 101.0, 99.5, 100.5, 1000],
        [1704097200, 101.5, 102.5, 100.5, 101.0, 1100],
        [1704097500, 102.0, 103.0, 101.0, 102.5, 1200]
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = temp_dir + "/"
        symbol = "TYPETEST"
        
        # Process and save data
        process_symbol_data(test_data, temp_path, symbol)
        
        # Read data back using updated read_from_csv
        data_tuple = read_from_csv(symbol, temp_path)
        
        # Verify DataTuple structure
        assert len(data_tuple) == 7, f"DataTuple should have 7 elements, got {len(data_tuple)}"
        symbol_name, timestamps, opens, highs, lows, closes, volume = data_tuple
        
        # Test timestamp array type
        assert isinstance(timestamps, np.ndarray), "Timestamps should be numpy array"
        assert timestamps.dtype == np.int64, f"Timestamps should be int64, got {timestamps.dtype}"
        print(f"✓ Timestamps have correct type: {timestamps.dtype}")
        
        # Test price arrays types (should be float64 for numba compatibility)
        price_arrays = [opens, highs, lows, closes]
        price_names = ['opens', 'highs', 'lows', 'closes']
        
        for arr, name in zip(price_arrays, price_names):
            assert isinstance(arr, np.ndarray), f"{name} should be numpy array"
            assert arr.dtype == np.float64, f"{name} should be float64, got {arr.dtype}"
            print(f"✓ {name} has correct type: {arr.dtype}")
        
        # Test volume array type (should be int64 for numba compatibility)
        assert isinstance(volume, np.ndarray), "Volume should be numpy array"
        assert volume.dtype == np.int64, f"Volume should be int64, got {volume.dtype}"
        print(f"✓ Volume has correct type: {volume.dtype}")
        
        # Verify all arrays have the same length
        array_lengths = [len(arr) for arr in [timestamps, opens, highs, lows, closes, volume]]
        assert all(length == array_lengths[0] for length in array_lengths), \
            f"All arrays should have same length, got {array_lengths}"
        print(f"✓ All arrays have consistent length: {array_lengths[0]}")
        
        # Test numba compatibility by checking if types are in allowed list
        numba_compatible_types = [np.int64, np.float64]
        all_arrays = [timestamps, opens, highs, lows, closes, volume]
        all_names = ['timestamps', 'opens', 'highs', 'lows', 'closes', 'volume']
        
        for arr, name in zip(all_arrays, all_names):
            assert arr.dtype in numba_compatible_types, \
                f"{name} has non-numba-compatible type: {arr.dtype}"
        print("✓ All arrays have numba-compatible types")
        
        # Verify data integrity (values should be preserved)
        assert len(timestamps) == len(test_data), "Data length should be preserved"
        for i in range(len(test_data)):
            assert timestamps[i] == test_data[i][0], f"Timestamp {i} not preserved"
            assert opens[i] == test_data[i][1], f"Open {i} not preserved"
            assert highs[i] == test_data[i][2], f"High {i} not preserved"
            assert lows[i] == test_data[i][3], f"Low {i} not preserved"
            assert closes[i] == test_data[i][4], f"Close {i} not preserved"
            assert volume[i] == test_data[i][5], f"Volume {i} not preserved"
        print("✓ All data values preserved correctly")
    
    print("Data type consistency test passed!")

if __name__ == "__main__":
    test_data_type_consistency()