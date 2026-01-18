"""
Test for helper function correctness.
"""

from datetime import datetime, timezone, timedelta
from datetime_utils import (
    is_market_hours, is_opening_hour, is_closing_hour,
    extract_hour, extract_minute, IST_OFFSET_SECONDS
)

# IST timezone for reference
IST = timezone(timedelta(seconds=IST_OFFSET_SECONDS))

def test_helper_function_correctness():
    """
    Property 8: Helper function correctness
    **Validates: Requirements 1.5**
    
    For any common time-based condition (market hours, etc.), helper functions 
    should correctly identify timestamps that meet the specified time criteria.
    """
    # Feature: numba-optimized-datetime, Property 8: Helper function correctness
    
    print("Testing helper function correctness...")
    
    # Test cases with known timestamps and expected results
    test_cases = [
        # Market hours tests (9:15 AM - 3:30 PM IST)
        {
            "timestamp": 1704096900,  # 2024-01-01 13:45:00 IST (within market hours)
            "expected_market": True,
            "expected_opening": False,
            "expected_closing": False,
            "description": "Afternoon market hours"
        },
        {
            "timestamp": 1704082200,  # 2024-01-01 09:30:00 IST (opening hour)
            "expected_market": True,
            "expected_opening": True,
            "expected_closing": False,
            "description": "Opening hour"
        },
        {
            "timestamp": 1704101400,  # 2024-01-01 15:00:00 IST (closing hour)
            "expected_market": True,
            "expected_opening": False,
            "expected_closing": True,
            "description": "Closing hour"
        },
        {
            "timestamp": 1704078600,  # 2024-01-01 08:30:00 IST (before market)
            "expected_market": False,
            "expected_opening": False,
            "expected_closing": False,
            "description": "Before market hours"
        },
        {
            "timestamp": 1704103200,  # 2024-01-01 15:30:00 IST (market close)
            "expected_market": True,  # 15:30 is still within market hours (inclusive)
            "expected_opening": False,
            "expected_closing": True,
            "description": "Market close time"
        },
        {
            "timestamp": 1704103800,  # 2024-01-01 15:40:00 IST (after market)
            "expected_market": False,
            "expected_opening": False,
            "expected_closing": False,
            "description": "After market hours"
        }
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {case['description']}")
        
        timestamp = case['timestamp']
        
        # Get human-readable time for debugging
        dt = datetime.fromtimestamp(timestamp, tz=IST)
        time_str = dt.strftime('%H:%M:%S')
        print(f"  Timestamp {timestamp} = {time_str} IST")
        
        # Test is_market_hours
        market_result = is_market_hours(timestamp)
        assert market_result == case['expected_market'], \
            f"is_market_hours failed for {case['description']}: got {market_result}, expected {case['expected_market']}"
        print(f"  ✓ is_market_hours: {market_result}")
        
        # Test is_opening_hour
        opening_result = is_opening_hour(timestamp)
        assert opening_result == case['expected_opening'], \
            f"is_opening_hour failed for {case['description']}: got {opening_result}, expected {case['expected_opening']}"
        print(f"  ✓ is_opening_hour: {opening_result}")
        
        # Test is_closing_hour
        closing_result = is_closing_hour(timestamp)
        assert closing_result == case['expected_closing'], \
            f"is_closing_hour failed for {case['description']}: got {closing_result}, expected {case['expected_closing']}"
        print(f"  ✓ is_closing_hour: {closing_result}")
    
    # Test edge cases
    print("\nTesting edge cases...")
    
    # Test market open (9:15 AM exactly)
    market_open_timestamp = 1704081300  # 2024-01-01 09:15:00 IST
    assert is_market_hours(market_open_timestamp) == True, "Market should be open at 9:15 AM"
    assert is_opening_hour(market_open_timestamp) == True, "9:15 AM should be opening hour"
    print("✓ Market open time (9:15 AM) correctly identified")
    
    # Test market close (3:30 PM exactly)
    market_close_timestamp = 1704103200  # 2024-01-01 15:30:00 IST
    assert is_market_hours(market_close_timestamp) == True, "Market should be open at 3:30 PM"
    assert is_closing_hour(market_close_timestamp) == True, "3:30 PM should be closing hour"
    print("✓ Market close time (3:30 PM) correctly identified")
    
    # Test consistency with time extraction functions
    print("\nTesting consistency with time extraction...")
    
    for case in test_cases:
        timestamp = case['timestamp']
        hour = extract_hour(timestamp)
        minute = extract_minute(timestamp)
        
        # Manual calculation for market hours
        current_minutes = hour * 60 + minute
        market_start_minutes = 9 * 60 + 15  # 9:15 AM
        market_end_minutes = 15 * 60 + 30   # 3:30 PM
        
        expected_in_market = market_start_minutes <= current_minutes <= market_end_minutes
        actual_in_market = is_market_hours(timestamp)
        
        assert actual_in_market == expected_in_market, \
            f"Market hours calculation inconsistent for {hour:02d}:{minute:02d}"
    
    print("✓ All helper functions are consistent with time extraction")
    
    print("\nHelper function correctness test passed!")

if __name__ == "__main__":
    test_helper_function_correctness()