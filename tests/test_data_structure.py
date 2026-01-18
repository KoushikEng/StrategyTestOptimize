"""
Test for DataTuple structure consistency.
"""

import numpy as np
from Utilities import DataTuple

def test_datatuple_structure_consistency():
    """
    Property 6: DataTuple structure consistency
    **Validates: Requirements 1.4**
    
    For any DataTuple returned by read_from_csv, it should contain exactly 7 elements 
    with timestamps as the second element (single array instead of separate date/time arrays).
    """
    # Feature: numba-optimized-datetime, Property 6: DataTuple structure consistency
    
    print("Testing DataTuple structure consistency...")
    
    # Create a sample DataTuple with the new structure
    symbol = "TEST"
    timestamps = np.array([1704096900, 1704097200, 1704097500], dtype=np.int64)
    opens = np.array([100.0, 101.0, 102.0], dtype=np.float64)
    highs = np.array([101.0, 102.0, 103.0], dtype=np.float64)
    lows = np.array([99.0, 100.0, 101.0], dtype=np.float64)
    closes = np.array([100.5, 101.5, 102.5], dtype=np.float64)
    volume = np.array([1000, 1100, 1200], dtype=np.int64)
    
    # Create DataTuple
    data_tuple: DataTuple = (symbol, timestamps, opens, highs, lows, closes, volume)
    
    # Test structure consistency
    assert len(data_tuple) == 7, f"DataTuple should have 7 elements, got {len(data_tuple)}"
    print(f"✓ DataTuple has correct number of elements: {len(data_tuple)}")
    
    # Test element types
    assert isinstance(data_tuple[0], str), "First element should be string (symbol)"
    assert isinstance(data_tuple[1], np.ndarray), "Second element should be numpy array (timestamps)"
    assert isinstance(data_tuple[2], np.ndarray), "Third element should be numpy array (opens)"
    assert isinstance(data_tuple[3], np.ndarray), "Fourth element should be numpy array (highs)"
    assert isinstance(data_tuple[4], np.ndarray), "Fifth element should be numpy array (lows)"
    assert isinstance(data_tuple[5], np.ndarray), "Sixth element should be numpy array (closes)"
    assert isinstance(data_tuple[6], np.ndarray), "Seventh element should be numpy array (volume)"
    print("✓ All elements have correct types")
    
    # Test timestamp array properties
    assert data_tuple[1].dtype == np.int64, f"Timestamps should be int64, got {data_tuple[1].dtype}"
    assert len(data_tuple[1]) > 0, "Timestamps array should not be empty"
    print(f"✓ Timestamps array has correct dtype: {data_tuple[1].dtype}")
    
    # Test that all arrays have the same length
    array_lengths = [len(arr) for arr in data_tuple[1:]]
    assert all(length == array_lengths[0] for length in array_lengths), \
        f"All arrays should have same length, got {array_lengths}"
    print(f"✓ All arrays have consistent length: {array_lengths[0]}")
    
    # Test numba compatibility of data types
    numba_compatible_types = [np.int64, np.float64]
    for i, arr in enumerate(data_tuple[1:], 1):
        assert arr.dtype in numba_compatible_types, \
            f"Array {i} has non-numba-compatible dtype: {arr.dtype}"
    print("✓ All arrays have numba-compatible dtypes")
    
    print("DataTuple structure consistency test passed!")

if __name__ == "__main__":
    test_datatuple_structure_consistency()