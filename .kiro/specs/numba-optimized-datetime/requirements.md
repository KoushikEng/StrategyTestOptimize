# Numba-Optimized Datetime Handling Requirements

## Overview
Optimize the `hist_download` function and related data processing to improve performance with numba by storing raw Unix timestamps and providing utility functions for time component extraction, eliminating string conversions entirely.

## User Stories

### 1. Performance Optimization
**As a** strategy developer  
**I want** datetime handling optimized for numba compilation  
**So that** my strategy backtests run significantly faster

### 2. Raw Timestamp Storage
**As a** strategy developer  
**I want** timestamps stored as raw Unix integers  
**So that** I get maximum performance with minimal overhead

### 3. Time Component Access
**As a** strategy developer with time-dependent logic  
**I want** fast utility functions to extract time components  
**So that** I can implement intraday timing rules without performance penalties

## Acceptance Criteria

### 1.1 Raw Timestamp Storage (Hybrid Approach)
- [ ] Store Unix timestamps as int64 in CSV files (single column)
- [ ] Eliminate all string datetime conversions from data processing
- [ ] Maintain timezone handling during data download only
- [ ] Use header format: `timestamp,Open,High,Low,Close,Volume`

### 1.2 Numba-Optimized Utility Functions
- [ ] Provide `@numba.jit` compiled function to extract hour from timestamp
- [ ] Provide `@numba.jit` compiled function to extract minute from timestamp  
- [ ] Provide `@numba.jit` compiled function to extract second from timestamp
- [ ] Provide `@numba.jit` compiled function to extract day of week from timestamp
- [ ] Provide `@numba.jit` compiled function to check if timestamp is within time range

### 1.3 Data Processing Performance
- [ ] Remove string datetime conversions from `process_symbol_data`
- [ ] Store raw timestamps directly in CSV without conversion
- [ ] Ensure all timestamp operations are numba-compatible
- [ ] Process data using integer arithmetic only

### 1.4 Updated Data Structures
- [ ] Update `DataTuple` to use single timestamp array instead of separate date/time
- [ ] Modify `read_from_csv` to return timestamp array as int64
- [ ] Ensure all arrays are numba-compatible types (np.int64, np.float64)
- [ ] Remove datetime object dependencies from data pipeline

### 1.5 Strategy Integration Support
- [ ] Provide example usage of time utility functions in strategies
- [ ] Create helper functions for common time-based conditions (market hours, etc.)
- [ ] Update strategy base classes to work with new timestamp format
- [ ] Ensure strategies can access time components efficiently when needed

### 1.6 Performance Validation
- [ ] Benchmark timestamp operations before and after optimization
- [ ] Verify numba compilation works with all timestamp functions
- [ ] Measure memory usage reduction from single timestamp column
- [ ] Test strategy execution speed improvements

## Technical Requirements

### Performance Goals
- Achieve 2-5x speedup in strategy execution with numba compilation
- Eliminate string parsing overhead in data loading
- Minimize memory allocations during timestamp operations
- Reduce CSV file size by using single timestamp column

### Data Format Requirements
- Timestamps stored as int64 Unix epoch (seconds since 1970-01-01)
- All price/volume data as float64/int64 for numba compatibility
- Maintain timezone information in download process only
- CSV format: `timestamp,Open,High,Low,Close,Volume`

### Hybrid Approach Benefits
- **Storage efficiency**: Single timestamp column vs separate date/time
- **Performance**: Raw integers for maximum numba speed
- **Flexibility**: Utility functions provide time components when needed
- **Simplicity**: No configuration options, single optimized approach

## Out of Scope
- Backward compatibility with existing string-based CSV files
- Supporting non-Unix timestamp formats
- Real-time data streaming optimizations
- Database storage alternatives
- Migration tools for legacy data