# Requirements Document

## Introduction

This document specifies the requirements for enhancing the Base strategy class with a backtesting.py-inspired interface. The enhancement aims to simplify strategy development by providing a clean, intuitive interface with efficient indicator management, automatic look-ahead prevention, and built-in position management while maintaining compatibility with existing numba optimizations.

## Glossary

- **Base_Strategy**: The enhanced base class for all trading strategies
- **Indicator_Wrapper**: A wrapper class that provides array-like access to pre-calculated indicator values
- **Position_Manager**: Component responsible for tracking and managing trading positions
- **Data_Slicer**: Component that automatically caps data access at the current bar index
- **Strategy_Context**: The execution context that maintains current bar index and strategy state
- **Indicator_Calculator**: External functions that compute technical indicators (SMA, EMA, etc.)
- **Look_Ahead_Prevention**: Mechanism that prevents strategies from accessing future data

## Requirements

### Requirement 1: Clean Strategy Interface

**User Story:** As a strategy developer, I want to use simple `init()` and `next()` methods instead of complex `run()` methods, so that I can focus on strategy logic rather than implementation details.

#### Acceptance Criteria

1. THE Base_Strategy SHALL provide an `init()` method for strategy initialization
2. THE Base_Strategy SHALL provide a `next()` method for processing each bar
3. THE Base_Strategy SHALL execute `init()` once before processing any bars
4. WHEN processing data, THE Base_Strategy SHALL call `next()` for each bar in sequence
5. THE Base_Strategy SHALL replace the legacy `run()` method with the new interface

### Requirement 2: Efficient Indicator Management

**User Story:** As a strategy developer, I want indicators to be pre-calculated once and then sliced dynamically, so that I can achieve better performance without recalculating indicators on every iteration.

#### Acceptance Criteria

1. THE Base_Strategy SHALL provide an `I()` method for registering indicators during initialization
2. WHEN an indicator is registered, THE Base_Strategy SHALL calculate the complete indicator series once
3. THE Indicator_Wrapper SHALL provide dynamic slicing to the current bar index
4. THE Base_Strategy SHALL store indicator results in memory for efficient access
5. WHEN accessing indicators during `next()`, THE system SHALL return pre-calculated values without recalculation

### Requirement 3: Look-Ahead Prevention

**User Story:** As a strategy developer, I want automatic data capping at the current bar index, so that I cannot accidentally use future data in my strategy logic.

#### Acceptance Criteria

1. WHEN accessing data arrays during `next()`, THE Data_Slicer SHALL limit access to bars up to the current index
2. WHEN accessing indicator values, THE Indicator_Wrapper SHALL prevent access to future values
3. IF a strategy attempts to access future data, THE system SHALL return only available data up to current index
4. THE Strategy_Context SHALL maintain the current bar index throughout execution
5. THE system SHALL ensure no look-ahead bias in strategy calculations

### Requirement 4: Position Management

**User Story:** As a strategy developer, I want built-in buy/sell methods and position tracking, so that I can manage positions without implementing complex position logic.

#### Acceptance Criteria

1. THE Base_Strategy SHALL provide a `buy()` method for opening long positions
2. THE Base_Strategy SHALL provide a `sell()` method for closing positions
3. THE Position_Manager SHALL track current position state (long, flat, short)
4. WHEN a position is opened, THE Position_Manager SHALL record entry price and timestamp
5. WHEN a position is closed, THE Position_Manager SHALL calculate and record the return
6. THE Base_Strategy SHALL provide access to current position information

### Requirement 5: Array-Like Indicator Access

**User Story:** As a strategy developer, I want natural array-like access to indicators using syntax like `indicator[-1]` and `indicator.values`, so that I can write intuitive and readable strategy code.

#### Acceptance Criteria

1. THE Indicator_Wrapper SHALL support negative indexing (e.g., `indicator[-1]` for current value)
2. THE Indicator_Wrapper SHALL support positive indexing relative to current position
3. THE Indicator_Wrapper SHALL provide a `values` property for accessing the underlying array
4. WHEN accessing `indicator[-1]`, THE system SHALL return the value at the current bar
5. WHEN accessing `indicator[-2]`, THE system SHALL return the value at the previous bar
6. THE Indicator_Wrapper SHALL raise appropriate errors for invalid index access

### Requirement 6: Numba Compatibility

**User Story:** As a performance-conscious developer, I want the enhanced interface to maintain compatibility with existing numba optimizations, so that I can achieve high-performance strategy execution.

#### Acceptance Criteria

1. THE Base_Strategy SHALL maintain compatibility with numba-compiled indicator functions
2. THE system SHALL support numba-optimized data processing where applicable
3. WHEN using numba-compiled indicators, THE system SHALL preserve performance characteristics
4. THE enhanced interface SHALL not introduce performance regressions compared to the current implementation
5. THE system SHALL allow strategies to opt into numba optimizations when available

### Requirement 7: Data Structure Compatibility

**User Story:** As a developer working with existing systems, I want the enhanced Base strategy to work with the current DataTuple format, so that I don't need to modify existing data pipelines.

#### Acceptance Criteria

1. THE Base_Strategy SHALL accept DataTuple format as input: (symbol, timestamps, opens, highs, lows, closes, volume)
2. THE Base_Strategy SHALL provide convenient access to price data (Open, High, Low, Close, Volume)
3. THE system SHALL maintain timestamp handling for time-based strategy logic
4. THE Base_Strategy SHALL expose data through a clean interface (e.g., `self.data.Close`, `self.data.Volume`)
5. THE system SHALL preserve all existing data type specifications (np.float64 for prices, np.int64 for timestamps and volume)

### Requirement 8: Strategy Execution Engine

**User Story:** As a strategy framework user, I want a robust execution engine that processes strategies efficiently, so that I can backtest strategies reliably across different market conditions.

#### Acceptance Criteria

1. THE execution engine SHALL iterate through all bars in the dataset sequentially
2. WHEN processing each bar, THE engine SHALL update the current index in Strategy_Context
3. THE engine SHALL call the strategy's `next()` method for each bar after initialization
4. THE engine SHALL collect and aggregate position returns throughout execution
5. THE engine SHALL provide the same output format as the current `process()` method: (returns, equity_curve, win_rate, no_of_trades)

### Requirement 9: Error Handling and Validation

**User Story:** As a strategy developer, I want clear error messages and validation, so that I can quickly identify and fix issues in my strategy implementation.

#### Acceptance Criteria

1. WHEN indicator registration fails, THE system SHALL provide descriptive error messages
2. WHEN invalid parameters are passed to indicators, THE system SHALL validate and report errors
3. IF a strategy accesses invalid array indices, THE system SHALL handle gracefully with appropriate errors
4. THE system SHALL validate that required methods (`init()`, `next()`) are implemented
5. WHEN position management operations fail, THE system SHALL provide clear error feedback