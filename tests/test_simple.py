"""
Simple test to verify datetime utility functions work correctly.
"""

from datetime import datetime, timezone, timedelta
from datetime_utils import extract_hour, extract_minute, extract_second, extract_day_of_week, is_in_time_range, IST_OFFSET_SECONDS

# IST timezone for reference
IST = timezone(timedelta(seconds=IST_OFFSET_SECONDS))

def test_extract_hour():
    """Test hour extraction against datetime library."""
    test_timestamps = [1704096900, 1609459200, 1577836800]  # Various timestamps
    
    for timestamp in test_timestamps:
        numba_hour = extract_hour(timestamp)
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        expected_hour = dt.hour
        
        print(f"Timestamp {timestamp}: numba={numba_hour}, datetime={expected_hour}")
        assert numba_hour == expected_hour, f"Hour mismatch: {numba_hour} != {expected_hour}"
        assert 0 <= numba_hour <= 23, f"Hour out of range: {numba_hour}"
    
    print("✓ Hour extraction test passed")

def test_extract_minute():
    """Test minute extraction against datetime library."""
    test_timestamps = [1704096900, 1609459200, 1577836800]
    
    for timestamp in test_timestamps:
        numba_minute = extract_minute(timestamp)
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        expected_minute = dt.minute
        
        print(f"Timestamp {timestamp}: numba={numba_minute}, datetime={expected_minute}")
        assert numba_minute == expected_minute, f"Minute mismatch: {numba_minute} != {expected_minute}"
        assert 0 <= numba_minute <= 59, f"Minute out of range: {numba_minute}"
    
    print("✓ Minute extraction test passed")

def test_extract_second():
    """Test second extraction against datetime library."""
    test_timestamps = [1704096900, 1609459200, 1577836800]
    
    for timestamp in test_timestamps:
        numba_second = extract_second(timestamp)
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        expected_second = dt.second
        
        print(f"Timestamp {timestamp}: numba={numba_second}, datetime={expected_second}")
        assert numba_second == expected_second, f"Second mismatch: {numba_second} != {expected_second}"
        assert 0 <= numba_second <= 59, f"Second out of range: {numba_second}"
    
    print("✓ Second extraction test passed")

if __name__ == "__main__":
    test_extract_hour()
    test_extract_minute()
    test_extract_second()
    print("All tests passed!")