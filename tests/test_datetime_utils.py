"""
Property-based tests for numba-optimized datetime utility functions.

This module contains property-based tests to verify the correctness of timestamp
utility functions against standard datetime library calculations.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings
from datetime_utils import (
    extract_hour, extract_minute, extract_second, extract_day_of_week,
    is_in_time_range, IST_OFFSET_SECONDS
)

# IST timezone for reference calculations
IST = timezone(timedelta(seconds=IST_OFFSET_SECONDS))

# Strategy for generating valid Unix timestamps
# Using range from 2000-01-01 to 2030-12-31 to avoid edge cases
timestamp_strategy = st.integers(
    min_value=946684800,   # 2000-01-01 00:00:00 UTC
    max_value=1924905600   # 2030-12-31 00:00:00 UTC
)

class TestTimeExtractionAccuracy:
    """Property tests for time extraction accuracy."""
    
    @given(timestamp_strategy)
    @settings(max_examples=200)
    def test_extract_hour_property(self, timestamp):
        """
        Property 1: Time extraction accuracy - Hour extraction
        **Validates: Requirements 1.2**
        
        For any valid Unix timestamp, extract_hour should produce
        mathematically correct results equivalent to datetime library.
        """
        # Feature: numba-optimized-datetime, Property 1: Time extraction accuracy
        
        # Get result from our numba function
        numba_hour = extract_hour(timestamp)
        
        # Get expected result from standard datetime library
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        expected_hour = dt.hour
        
        assert numba_hour == expected_hour, (
            f"Hour extraction mismatch for timestamp {timestamp}: "
            f"numba={numba_hour}, datetime={expected_hour}"
        )
        assert 0 <= numba_hour <= 23, f"Hour out of range: {numba_hour}"
    
    @given(timestamp_strategy)
    @settings(max_examples=200)
    def test_extract_minute_property(self, timestamp):
        """
        Property 1: Time extraction accuracy - Minute extraction
        **Validates: Requirements 1.2**
        """
        # Feature: numba-optimized-datetime, Property 1: Time extraction accuracy
        
        numba_minute = extract_minute(timestamp)
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        expected_minute = dt.minute
        
        assert numba_minute == expected_minute, (
            f"Minute extraction mismatch for timestamp {timestamp}: "
            f"numba={numba_minute}, datetime={expected_minute}"
        )
        assert 0 <= numba_minute <= 59, f"Minute out of range: {numba_minute}"
    
    @given(timestamp_strategy)
    @settings(max_examples=200)
    def test_extract_second_property(self, timestamp):
        """
        Property 1: Time extraction accuracy - Second extraction
        **Validates: Requirements 1.2**
        """
        # Feature: numba-optimized-datetime, Property 1: Time extraction accuracy
        
        numba_second = extract_second(timestamp)
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        expected_second = dt.second
        
        assert numba_second == expected_second, (
            f"Second extraction mismatch for timestamp {timestamp}: "
            f"numba={numba_second}, datetime={expected_second}"
        )
        assert 0 <= numba_second <= 59, f"Second out of range: {numba_second}"
    
    @given(timestamp_strategy)
    @settings(max_examples=200)
    def test_extract_day_of_week_property(self, timestamp):
        """
        Property 1: Time extraction accuracy - Day of week extraction
        **Validates: Requirements 1.2**
        """
        # Feature: numba-optimized-datetime, Property 1: Time extraction accuracy
        
        numba_dow = extract_day_of_week(timestamp)
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        # datetime.weekday() returns 0=Monday, 6=Sunday (same as our function)
        expected_dow = dt.weekday()
        
        assert numba_dow == expected_dow, (
            f"Day of week extraction mismatch for timestamp {timestamp}: "
            f"numba={numba_dow}, datetime={expected_dow}"
        )
        assert 0 <= numba_dow <= 6, f"Day of week out of range: {numba_dow}"
    
    @given(
        timestamp_strategy,
        st.integers(min_value=0, max_value=23),  # start_hour
        st.integers(min_value=0, max_value=59),  # start_minute
        st.integers(min_value=0, max_value=23),  # end_hour
        st.integers(min_value=0, max_value=59)   # end_minute
    )
    @settings(max_examples=100)
    def test_is_in_time_range_property(self, timestamp, start_hour, start_minute, end_hour, end_minute):
        """
        Property 1: Time extraction accuracy - Time range checking
        **Validates: Requirements 1.2**
        """
        # Feature: numba-optimized-datetime, Property 1: Time extraction accuracy
        
        numba_result = is_in_time_range(timestamp, start_hour, start_minute, end_hour, end_minute)
        
        # Calculate expected result using datetime library
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        current_minutes = dt.hour * 60 + dt.minute
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute
        
        if start_minutes <= end_minutes:
            expected_result = start_minutes <= current_minutes <= end_minutes
        else:
            # Range crosses midnight
            expected_result = current_minutes >= start_minutes or current_minutes <= end_minutes
        
        assert numba_result == expected_result, (
            f"Time range check mismatch for timestamp {timestamp} "
            f"({dt.hour:02d}:{dt.minute:02d}) in range "
            f"{start_hour:02d}:{start_minute:02d}-{end_hour:02d}:{end_minute:02d}: "
            f"numba={numba_result}, expected={expected_result}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])