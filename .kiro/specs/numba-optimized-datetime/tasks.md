# Implementation Plan: Numba-Optimized Datetime Handling

## Overview

This implementation plan converts the numba-optimized datetime design into discrete coding tasks. The approach focuses on incremental development, starting with core utility functions, then updating data structures, modifying data processing, and finally integrating everything with comprehensive testing.

## Tasks

- [x] 1. Create numba utility functions module
  - [x] 1.1 Create new `datetime_utils.py` module with numba imports
    - Set up module structure with numba imports
    - Define timezone offset constants for local time calculations
    - _Requirements: 1.2_
  
  - [x] 1.2 Write property test for time extraction accuracy
    - **Property 1: Time extraction accuracy**
    - **Validates: Requirements 1.2**
  
  - [x] 1.3 Implement `extract_hour` function with @numba.jit decorator
    - Write function to extract hour (0-23) from Unix timestamp using integer arithmetic
    - Include timezone offset handling for local time
    - _Requirements: 1.2_
  
  - [x] 1.4 Implement `extract_minute` function with @numba.jit decorator
    - Write function to extract minute (0-59) from Unix timestamp
    - _Requirements: 1.2_
  
  - [x] 1.5 Implement `extract_second` function with @numba.jit decorator
    - Write function to extract second (0-59) from Unix timestamp
    - _Requirements: 1.2_
  
  - [x] 1.6 Implement `extract_day_of_week` function with @numba.jit decorator
    - Write function to extract day of week (0=Monday, 6=Sunday) from Unix timestamp
    - Use mathematical calculation: (days_since_epoch + 3) % 7
    - _Requirements: 1.2_
  
  - [x] 1.7 Implement `is_in_time_range` function with @numba.jit decorator
    - Write function to check if timestamp falls within specified time range
    - Handle edge cases like ranges crossing midnight
    - _Requirements: 1.2_
  
  - [x] 1.8 Write property test for numba compilation compatibility
    - **Property 2: Numba compilation compatibility**
    - **Validates: Requirements 1.2, 1.3, 1.6**

- [x] 2. Update data structures and type definitions
  - [x] 2.1 Modify DataTuple type alias in Utilities.py
    - Update from 8-element tuple to 7-element tuple
    - Change from (symbol, dates, times, opens, highs, lows, closes, volume) to (symbol, timestamps, opens, highs, lows, closes, volume)
    - _Requirements: 1.4_
  
  - [x] 2.2 Write property test for DataTuple structure consistency
    - **Property 6: DataTuple structure consistency**
    - **Validates: Requirements 1.4**

- [x] 3. Modify data processing functions
  - [x] 3.1 Update `process_symbol_data` function to eliminate string conversions
    - Remove datetime string formatting logic
    - Store raw Unix timestamps directly without conversion
    - Update CSV header to "timestamp,Open,High,Low,Close,Volume"
    - _Requirements: 1.1, 1.3_
  
  - [x] 3.2 Write property test for string operation elimination
    - **Property 4: String operation elimination**
    - **Validates: Requirements 1.1, 1.3, 1.4**
  
  - [x] 3.3 Update `read_from_csv` function for new timestamp format
    - Modify to read single timestamp column as int64
    - Remove date/time parsing logic
    - Return updated 7-element DataTuple structure
    - _Requirements: 1.4_
  
  - [x] 3.4 Write property test for data type consistency
    - **Property 3: Data type consistency**
    - **Validates: Requirements 1.3, 1.4**
  
  - [x] 3.5 Write property test for CSV format compliance
    - **Property 5: CSV format compliance**
    - **Validates: Requirements 1.1, 1.3**

- [x] 4. Checkpoint - Ensure core functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Create helper functions for common time-based conditions
  - [x] 5.1 Implement `is_market_hours` helper function
    - Create function to check if timestamp falls within market hours (9:15 AM - 3:30 PM IST)
    - Use existing time extraction utilities
    - _Requirements: 1.5_
  
  - [x] 5.2 Implement `is_opening_hour` helper function
    - Create function to check if timestamp is within first hour of market
    - _Requirements: 1.5_
  
  - [x] 5.3 Implement `is_closing_hour` helper function
    - Create function to check if timestamp is within last hour of market
    - _Requirements: 1.5_
  
  - [x] 5.4 Write property test for helper function correctness
    - **Property 8: Helper function correctness**
    - **Validates: Requirements 1.5**

- [x] 6. Update strategy base class for new timestamp format
  - [x] 6.1 Modify Base.py to handle updated DataTuple structure
    - Update any references to date/time arrays to use single timestamp array
    - Ensure process method works with new data structure
    - _Requirements: 1.5_
  
  - [x] 6.2 Write property test for strategy compatibility
    - **Property 7: Strategy compatibility**
    - **Validates: Requirements 1.5**

- [x] 7. Create vectorized utility functions for array operations
  - [x] 7.1 Implement vectorized versions of time extraction functions
    - Create `extract_hour_vectorized`, `extract_minute_vectorized`, etc.
    - Use numpy operations for processing entire timestamp arrays
    - Ensure numba compatibility for array operations
    - _Requirements: 1.5_
  
  - [x] 7.2 Write unit tests for vectorized functions
    - Test vectorized functions with various array sizes
    - Verify results match individual function calls
    - _Requirements: 1.5_

- [x] 8. Integration and compatibility testing
  - [x] 8.1 Update main.py to work with new data format
    - Ensure data loading and strategy execution work with updated DataTuple
    - Test with existing strategy examples
    - _Requirements: 1.5_
  
  - [x] 8.2 Write integration tests for end-to-end workflow
    - Test complete pipeline: download → store → load → execute strategy
    - Verify no string conversions occur during processing
    - _Requirements: 1.1, 1.3, 1.5_

- [x] 9. Final checkpoint - Comprehensive testing
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- All timestamp operations use integer arithmetic for maximum numba performance
- Timezone handling is isolated to the download phase only