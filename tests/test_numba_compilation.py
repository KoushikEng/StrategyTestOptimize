"""
Test for numba compilation compatibility of datetime utility functions.
"""

import numba
from datetime_utils import (
    extract_hour, extract_minute, extract_second, 
    extract_day_of_week, is_in_time_range
)

def test_numba_compilation_compatibility():
    """
    Property 2: Numba compilation compatibility
    **Validates: Requirements 1.2, 1.3, 1.6**
    
    For any timestamp utility function in the system, numba compilation 
    should succeed without errors and produce executable code.
    """
    # Feature: numba-optimized-datetime, Property 2: Numba compilation compatibility
    
    print("Testing numba compilation compatibility...")
    
    # Test extract_hour compilation
    try:
        compiled_hour = numba.jit(nopython=True)(extract_hour.py_func)
        result = compiled_hour(1704096900)
        print(f"✓ extract_hour compiled successfully, result: {result}")
        assert isinstance(result, int), "extract_hour should return int"
    except Exception as e:
        raise AssertionError(f"extract_hour failed to compile: {e}")
    
    # Test extract_minute compilation
    try:
        compiled_minute = numba.jit(nopython=True)(extract_minute.py_func)
        result = compiled_minute(1704096900)
        print(f"✓ extract_minute compiled successfully, result: {result}")
        assert isinstance(result, int), "extract_minute should return int"
    except Exception as e:
        raise AssertionError(f"extract_minute failed to compile: {e}")
    
    # Test extract_second compilation
    try:
        compiled_second = numba.jit(nopython=True)(extract_second.py_func)
        result = compiled_second(1704096900)
        print(f"✓ extract_second compiled successfully, result: {result}")
        assert isinstance(result, int), "extract_second should return int"
    except Exception as e:
        raise AssertionError(f"extract_second failed to compile: {e}")
    
    # Test extract_day_of_week compilation
    try:
        compiled_dow = numba.jit(nopython=True)(extract_day_of_week.py_func)
        result = compiled_dow(1704096900)
        print(f"✓ extract_day_of_week compiled successfully, result: {result}")
        assert isinstance(result, int), "extract_day_of_week should return int"
    except Exception as e:
        raise AssertionError(f"extract_day_of_week failed to compile: {e}")
    
    # Test is_in_time_range compilation
    try:
        compiled_range = numba.jit(nopython=True)(is_in_time_range.py_func)
        result = compiled_range(1704096900, 9, 15, 15, 30)
        print(f"✓ is_in_time_range compiled successfully, result: {result}")
        assert isinstance(result, bool), "is_in_time_range should return bool"
    except Exception as e:
        raise AssertionError(f"is_in_time_range failed to compile: {e}")
    
    print("All functions compiled successfully with numba!")

if __name__ == "__main__":
    test_numba_compilation_compatibility()
    print("Numba compilation test passed!")