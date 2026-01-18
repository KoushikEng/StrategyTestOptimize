"""
Unit tests for vectorized datetime utility functions.
"""

import numpy as np
from datetime_utils import (
    extract_hour, extract_minute, extract_second, extract_day_of_week,
    is_in_time_range, is_market_hours, is_opening_hour, is_closing_hour,
    extract_hour_vectorized, extract_minute_vectorized, extract_second_vectorized,
    extract_day_of_week_vectorized, is_in_time_range_vectorized,
    is_market_hours_vectorized, is_opening_hour_vectorized, is_closing_hour_vectorized
)

def test_vectorized_functions():
    """Test vectorized functions with various array sizes and verify results match individual function calls."""
    
    print("Testing vectorized datetime utility functions...")
    
    # Test data with various timestamps
    test_timestamps = np.array([
        1704081300,  # 2024-01-01 09:15:00 IST (market open)
        1704082200,  # 2024-01-01 09:30:00 IST (opening hour)
        1704096900,  # 2024-01-01 13:45:00 IST (afternoon)
        1704101400,  # 2024-01-01 15:00:00 IST (closing hour)
        1704103200,  # 2024-01-01 15:30:00 IST (market close)
        1704078600,  # 2024-01-01 08:30:00 IST (before market)
        1704103800   # 2024-01-01 15:40:00 IST (after market)
    ], dtype=np.int64)
    
    print(f"Testing with {len(test_timestamps)} timestamps...")
    
    # Test extract_hour_vectorized
    print("\nTesting extract_hour_vectorized...")
    vectorized_hours = extract_hour_vectorized(test_timestamps)
    individual_hours = np.array([extract_hour(ts) for ts in test_timestamps])
    
    assert np.array_equal(vectorized_hours, individual_hours), \
        f"Hour extraction mismatch: vectorized={vectorized_hours}, individual={individual_hours}"
    assert vectorized_hours.dtype == np.int64, f"Hours should be int64, got {vectorized_hours.dtype}"
    assert len(vectorized_hours) == len(test_timestamps), "Hours array length mismatch"
    print(f"✓ Hours: {vectorized_hours}")
    
    # Test extract_minute_vectorized
    print("\nTesting extract_minute_vectorized...")
    vectorized_minutes = extract_minute_vectorized(test_timestamps)
    individual_minutes = np.array([extract_minute(ts) for ts in test_timestamps])
    
    assert np.array_equal(vectorized_minutes, individual_minutes), \
        f"Minute extraction mismatch: vectorized={vectorized_minutes}, individual={individual_minutes}"
    assert vectorized_minutes.dtype == np.int64, f"Minutes should be int64, got {vectorized_minutes.dtype}"
    print(f"✓ Minutes: {vectorized_minutes}")
    
    # Test extract_second_vectorized
    print("\nTesting extract_second_vectorized...")
    vectorized_seconds = extract_second_vectorized(test_timestamps)
    individual_seconds = np.array([extract_second(ts) for ts in test_timestamps])
    
    assert np.array_equal(vectorized_seconds, individual_seconds), \
        f"Second extraction mismatch: vectorized={vectorized_seconds}, individual={individual_seconds}"
    assert vectorized_seconds.dtype == np.int64, f"Seconds should be int64, got {vectorized_seconds.dtype}"
    print(f"✓ Seconds: {vectorized_seconds}")
    
    # Test extract_day_of_week_vectorized
    print("\nTesting extract_day_of_week_vectorized...")
    vectorized_dow = extract_day_of_week_vectorized(test_timestamps)
    individual_dow = np.array([extract_day_of_week(ts) for ts in test_timestamps])
    
    assert np.array_equal(vectorized_dow, individual_dow), \
        f"Day of week extraction mismatch: vectorized={vectorized_dow}, individual={individual_dow}"
    assert vectorized_dow.dtype == np.int64, f"Day of week should be int64, got {vectorized_dow.dtype}"
    print(f"✓ Day of week: {vectorized_dow}")
    
    # Test is_in_time_range_vectorized
    print("\nTesting is_in_time_range_vectorized...")
    start_hour, start_minute = 9, 15
    end_hour, end_minute = 15, 30
    
    vectorized_in_range = is_in_time_range_vectorized(test_timestamps, start_hour, start_minute, end_hour, end_minute)
    individual_in_range = np.array([is_in_time_range(ts, start_hour, start_minute, end_hour, end_minute) for ts in test_timestamps])
    
    assert np.array_equal(vectorized_in_range, individual_in_range), \
        f"Time range check mismatch: vectorized={vectorized_in_range}, individual={individual_in_range}"
    assert vectorized_in_range.dtype == np.bool_, f"Time range should be bool, got {vectorized_in_range.dtype}"
    print(f"✓ In time range (9:15-15:30): {vectorized_in_range}")
    
    # Test is_market_hours_vectorized
    print("\nTesting is_market_hours_vectorized...")
    vectorized_market = is_market_hours_vectorized(test_timestamps)
    individual_market = np.array([is_market_hours(ts) for ts in test_timestamps])
    
    assert np.array_equal(vectorized_market, individual_market), \
        f"Market hours check mismatch: vectorized={vectorized_market}, individual={individual_market}"
    assert vectorized_market.dtype == np.bool_, f"Market hours should be bool, got {vectorized_market.dtype}"
    print(f"✓ Market hours: {vectorized_market}")
    
    # Test is_opening_hour_vectorized
    print("\nTesting is_opening_hour_vectorized...")
    vectorized_opening = is_opening_hour_vectorized(test_timestamps)
    individual_opening = np.array([is_opening_hour(ts) for ts in test_timestamps])
    
    assert np.array_equal(vectorized_opening, individual_opening), \
        f"Opening hour check mismatch: vectorized={vectorized_opening}, individual={individual_opening}"
    assert vectorized_opening.dtype == np.bool_, f"Opening hour should be bool, got {vectorized_opening.dtype}"
    print(f"✓ Opening hour: {vectorized_opening}")
    
    # Test is_closing_hour_vectorized
    print("\nTesting is_closing_hour_vectorized...")
    vectorized_closing = is_closing_hour_vectorized(test_timestamps)
    individual_closing = np.array([is_closing_hour(ts) for ts in test_timestamps])
    
    assert np.array_equal(vectorized_closing, individual_closing), \
        f"Closing hour check mismatch: vectorized={vectorized_closing}, individual={individual_closing}"
    assert vectorized_closing.dtype == np.bool_, f"Closing hour should be bool, got {vectorized_closing.dtype}"
    print(f"✓ Closing hour: {vectorized_closing}")
    
    # Test with different array sizes
    print("\nTesting with different array sizes...")
    
    for size in [1, 5, 10, 50, 100]:
        # Generate test timestamps
        base_timestamp = 1704081300  # 2024-01-01 09:15:00 IST
        test_array = np.arange(base_timestamp, base_timestamp + size * 300, 300, dtype=np.int64)  # 5-minute intervals
        
        # Test one function as representative
        vectorized_result = extract_hour_vectorized(test_array)
        individual_result = np.array([extract_hour(ts) for ts in test_array])
        
        assert np.array_equal(vectorized_result, individual_result), \
            f"Size {size} test failed"
        assert len(vectorized_result) == size, f"Result length mismatch for size {size}"
        
        print(f"✓ Array size {size} handled correctly")
    
    # Test empty array
    print("\nTesting empty array...")
    empty_timestamps = np.array([], dtype=np.int64)
    empty_hours = extract_hour_vectorized(empty_timestamps)
    
    assert len(empty_hours) == 0, "Empty array should return empty result"
    assert empty_hours.dtype == np.int64, "Empty result should maintain correct dtype"
    print("✓ Empty array handled correctly")
    
    # Test single element array
    print("\nTesting single element array...")
    single_timestamp = np.array([1704096900], dtype=np.int64)
    single_hour = extract_hour_vectorized(single_timestamp)
    expected_hour = extract_hour(1704096900)
    
    assert len(single_hour) == 1, "Single element should return single result"
    assert single_hour[0] == expected_hour, f"Single element result mismatch: {single_hour[0]} != {expected_hour}"
    print(f"✓ Single element array handled correctly: {single_hour[0]}")
    
    print("\nVectorized functions unit tests passed!")

if __name__ == "__main__":
    test_vectorized_functions()