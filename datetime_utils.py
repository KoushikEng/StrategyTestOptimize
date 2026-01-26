"""
Numba-optimized datetime utility functions for high-performance timestamp operations.

This module provides numba-compiled functions for extracting time components from Unix timestamps
and performing time-based operations without string conversions, optimized for strategy execution.
"""

from numba import njit
import numpy as np
from typing import Union
from numpy.typing import NDArray

# Timezone offset for IST (UTC+5:30) in seconds
IST_OFFSET_SECONDS = 19800  # 5.5 hours * 3600 seconds/hour

# Constants for time calculations
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24

# Unix epoch started on Thursday (1970-01-01)
# Adjustment to make Monday = 0 in day_of_week calculation
EPOCH_DAY_ADJUSTMENT = 3


@njit
def extract_hour(timestamp: int) -> int:
    """
    Extract hour (0-23) from Unix timestamp in IST timezone.
    
    Args:
        timestamp (int): Unix timestamp in seconds
        
    Returns:
        int: Hour component (0-23)
    """
    local_timestamp = timestamp + IST_OFFSET_SECONDS
    seconds_in_day = local_timestamp % SECONDS_PER_DAY
    return seconds_in_day // SECONDS_PER_HOUR


@njit
def extract_minute(timestamp: int) -> int:
    """
    Extract minute (0-59) from Unix timestamp.
    
    Args:
        timestamp (int): Unix timestamp in seconds
        
    Returns:
        int: Minute component (0-59)
    """
    local_timestamp = timestamp + IST_OFFSET_SECONDS
    seconds_in_day = local_timestamp % SECONDS_PER_DAY
    seconds_in_hour = seconds_in_day % SECONDS_PER_HOUR
    return seconds_in_hour // SECONDS_PER_MINUTE

@njit
def extract_second(timestamp: int) -> int:
    """
    Extract second (0-59) from Unix timestamp.
    
    Args:
        timestamp (int): Unix timestamp in seconds
        
    Returns:
        int: Second component (0-59)
    """
    local_timestamp = timestamp + IST_OFFSET_SECONDS
    return local_timestamp % SECONDS_PER_MINUTE


@njit
def extract_day_of_week(timestamp: int) -> int:
    """
    Extract day of week (0=Monday, 6=Sunday) from Unix timestamp.
    
    Args:
        timestamp (int): Unix timestamp in seconds
        
    Returns:
        int: Day of week (0=Monday, 1=Tuesday, ..., 6=Sunday)
    """
    local_timestamp = timestamp + IST_OFFSET_SECONDS
    days_since_epoch = local_timestamp // SECONDS_PER_DAY
    return (days_since_epoch + EPOCH_DAY_ADJUSTMENT) % 7


@njit
def is_in_time_range(timestamp: int, start_hour: int, start_minute: int, 
                     end_hour: int, end_minute: int) -> bool:
    """
    Check if timestamp falls within specified time range (IST timezone).
    
    Args:
        timestamp (int): Unix timestamp in seconds
        start_hour (int): Start hour (0-23)
        start_minute (int): Start minute (0-59)
        end_hour (int): End hour (0-23)
        end_minute (int): End minute (0-59)
        
    Returns:
        bool: True if timestamp is within the time range, False otherwise
    """
    hour = extract_hour(timestamp)
    minute = extract_minute(timestamp)
    
    current_minutes = hour * MINUTES_PER_HOUR + minute
    start_minutes = start_hour * MINUTES_PER_HOUR + start_minute
    end_minutes = end_hour * MINUTES_PER_HOUR + end_minute
    
    # Handle ranges that cross midnight
    if start_minutes <= end_minutes:
        return start_minutes <= current_minutes <= end_minutes
    else:
        return current_minutes >= start_minutes or current_minutes <= end_minutes


# Helper functions for common time-based conditions

@njit
def is_market_hours(timestamp: int) -> bool:
    """
    Check if timestamp falls within Indian market hours (9:15 AM - 3:30 PM IST).
    
    Args:
        timestamp (int): Unix timestamp in seconds
        
    Returns:
        bool: True if timestamp is within market hours, False otherwise
    """
    return is_in_time_range(timestamp, 9, 15, 15, 30)


@njit
def is_opening_hour(timestamp: int) -> bool:
    """
    Check if timestamp is within the first hour of market (9:15 AM - 10:15 AM IST).
    
    Args:
        timestamp (int): Unix timestamp in seconds
        
    Returns:
        bool: True if timestamp is within opening hour, False otherwise
    """
    return is_in_time_range(timestamp, 9, 15, 10, 15)


@njit
def is_closing_hour(timestamp: int) -> bool:
    """
    Check if timestamp is within the last hour of market (2:30 PM - 3:30 PM IST).
    
    Args:
        timestamp (int): Unix timestamp in seconds
        
    Returns:
        bool: True if timestamp is within closing hour, False otherwise
    """
    return is_in_time_range(timestamp, 14, 30, 15, 30)

# Vectorized utility functions for array operations

@njit
def extract_hour_vectorized(timestamps: NDArray) -> NDArray:
    """
    Extract hours (0-23) from array of Unix timestamps in IST timezone.
    
    Args:
        timestamps (NDArray): Array of Unix timestamps in seconds
        
    Returns:
        NDArray: Array of hour components (0-23)
    """
    return extract_hour(timestamps)


@njit
def extract_minute_vectorized(timestamps: NDArray) -> NDArray:
    """
    Extract minutes (0-59) from array of Unix timestamps.
    
    Args:
        timestamps (NDArray): Array of Unix timestamps in seconds
        
    Returns:
        NDArray: Array of minute components (0-59)
    """
    return extract_minute(timestamps)


@njit
def extract_second_vectorized(timestamps: NDArray) -> NDArray:
    """
    Extract seconds (0-59) from array of Unix timestamps.
    
    Args:
        timestamps (NDArray): Array of Unix timestamps in seconds
        
    Returns:
        NDArray: Array of second components (0-59)
    """
    return extract_second(timestamps)


@njit
def extract_day_of_week_vectorized(timestamps: NDArray) -> NDArray:
    """
    Extract day of week (0=Monday, 6=Sunday) from array of Unix timestamps.
    
    Args:
        timestamps (NDArray): Array of Unix timestamps in seconds
        
    Returns:
        NDArray: Array of day of week components (0=Monday, 1=Tuesday, ..., 6=Sunday)
    """
    return extract_day_of_week(timestamps)


@njit
def is_in_time_range_vectorized(timestamps: NDArray, start_hour: int, start_minute: int, 
                                end_hour: int, end_minute: int) -> NDArray:
    """
    Check if timestamps fall within specified time range (IST timezone).
    
    Args:
        timestamps (NDArray): Array of Unix timestamps in seconds
        start_hour (int): Start hour (0-23)
        start_minute (int): Start minute (0-59)
        end_hour (int): End hour (0-23)
        end_minute (int): End minute (0-59)
        
    Returns:
        NDArray: Boolean array indicating which timestamps are within the time range
    """
    result = np.empty(len(timestamps), dtype=np.bool_)
    for i in range(len(timestamps)):
        result[i] = is_in_time_range(timestamps[i], start_hour, start_minute, end_hour, end_minute)
    return result


@njit
def is_market_hours_vectorized(timestamps: NDArray) -> NDArray:
    """
    Check if timestamps fall within Indian market hours (9:15 AM - 3:30 PM IST).
    
    Args:
        timestamps (NDArray): Array of Unix timestamps in seconds
        
    Returns:
        NDArray: Boolean array indicating which timestamps are within market hours
    """
    result = np.empty(len(timestamps), dtype=np.bool_)
    for i in range(len(timestamps)):
        result[i] = is_market_hours(timestamps[i])
    return result


@njit
def is_opening_hour_vectorized(timestamps: NDArray) -> NDArray:
    """
    Check if timestamps are within the first hour of market (9:15 AM - 10:15 AM IST).
    
    Args:
        timestamps (NDArray): Array of Unix timestamps in seconds
        
    Returns:
        NDArray: Boolean array indicating which timestamps are within opening hour
    """
    result = np.empty(len(timestamps), dtype=np.bool_)
    for i in range(len(timestamps)):
        result[i] = is_opening_hour(timestamps[i])
    return result


@njit
def is_closing_hour_vectorized(timestamps: NDArray) -> NDArray:
    """
    Check if timestamps are within the last hour of market (2:30 PM - 3:30 PM IST).
    
    Args:
        timestamps (NDArray): Array of Unix timestamps in seconds
        
    Returns:
        NDArray: Boolean array indicating which timestamps are within closing hour
    """
    result = np.empty(len(timestamps), dtype=np.bool_)
    for i in range(len(timestamps)):
        result[i] = is_closing_hour(timestamps[i])
    return result