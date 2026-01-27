# Requirements Document

## Introduction

The research_agent/compiler.py currently generates trading strategies using an outdated pattern that conflicts with the enhanced Base strategy framework. The compiler generates strategies with manual `run()` methods, direct indicator calculations, and manual position tracking, while the enhanced framework uses a clean `init()` and `next()` interface with built-in position management and indicator registration.

## Glossary

- **Compiler**: The research_agent/compiler.py module that transforms StrategySpec JSON into executable Python strategy classes
- **Enhanced_Base**: The new Base class framework using init() and next() methods with built-in position management
- **StrategySpec**: JSON specification format defining strategy indicators, conditions, and parameters
- **Indicator_Registration**: The self.I() method for registering indicators in the enhanced framework
- **Data_Accessor**: The self.data interface providing OHLCV access with automatic slicing
- **Position_Manager**: Built-in position tracking through self.position property and buy()/sell() methods
- **DateTime_Utils**: Time-based filtering functions from datetime_utils module

## Requirements

### Requirement 1: Enhanced Framework Compatibility

**User Story:** As a strategy developer, I want the compiler to generate strategies compatible with the enhanced Base framework, so that generated strategies use modern patterns and built-in capabilities.

#### Acceptance Criteria

1. WHEN the compiler generates a strategy THEN the strategy SHALL inherit from the enhanced Base class
2. WHEN the compiler generates strategy methods THEN the strategy SHALL implement init() and next() methods instead of run()
3. WHEN the compiler processes StrategySpec indicators THEN the strategy SHALL register indicators using self.I() in the init() method
4. WHEN the compiler generates trading logic THEN the strategy SHALL use self.buy() and self.sell() methods for position management
5. WHEN the compiler generates data access code THEN the strategy SHALL use self.data.Close[-1], self.data.Volume[-1] patterns

### Requirement 2: Indicator Registration System

**User Story:** As a strategy developer, I want indicators to be properly registered using the enhanced framework, so that indicators are calculated once and cached efficiently.

#### Acceptance Criteria

1. WHEN the compiler processes indicator specifications THEN the compiler SHALL generate self.I() calls in the init() method
2. WHEN multiple indicators are specified THEN each indicator SHALL be registered as a separate self.I() call
3. WHEN indicators have parameters THEN the parameters SHALL be passed correctly to the indicator function
4. WHEN indicators return multiple values THEN the compiler SHALL handle composite indicator access patterns
5. WHEN indicator functions are missing THEN the compiler SHALL trigger the Librarian system to create them

### Requirement 3: Data Access Pattern Generation

**User Story:** As a strategy developer, I want generated strategies to use the enhanced data access patterns, so that strategies can access OHLCV data safely without look-ahead bias.

#### Acceptance Criteria

1. WHEN the compiler generates condition expressions THEN expressions SHALL use self.data.Close[-1] instead of closes[i]
2. WHEN accessing historical data THEN the compiler SHALL use negative indexing patterns like self.data.Close[-2]
3. WHEN accessing current bar data THEN the compiler SHALL use [-1] indexing for current values
4. WHEN accessing indicator values THEN the compiler SHALL use registered indicator names with [-1] indexing
5. WHEN generating volume access THEN the compiler SHALL use self.data.Volume[-1] pattern

### Requirement 4: Position Management Integration

**User Story:** As a strategy developer, I want generated strategies to use built-in position management, so that position tracking is handled automatically without manual state management.

#### Acceptance Criteria

1. WHEN entry conditions are met THEN the strategy SHALL call self.buy() instead of manual position tracking
2. WHEN exit conditions are met THEN the strategy SHALL call self.sell() instead of manual return calculations
3. WHEN checking position status THEN the strategy SHALL use self.position property instead of in_position variables
4. WHEN the compiler generates trading logic THEN manual position tracking variables SHALL NOT be created
5. WHEN position sizing is specified THEN the size parameter SHALL be passed to self.buy()

### Requirement 5: Time-Based Logic Support

**User Story:** As a strategy developer, I want generated strategies to support time-based filtering, so that strategies can implement time-aware trading logic using datetime utilities.

#### Acceptance Criteria

1. WHEN time-based conditions are specified THEN the compiler SHALL import datetime_utils functions
2. WHEN market hours filtering is needed THEN the compiler SHALL use is_market_hours() with timestamp access
3. WHEN custom time ranges are specified THEN the compiler SHALL use is_in_time_range() function
4. WHEN accessing timestamps THEN the compiler SHALL use self.data.timestamps[-1] for current timestamp
5. WHEN time-based logic is used THEN the compiler SHALL handle raw Unix timestamp format correctly

### Requirement 6: Template Structure Modernization

**User Story:** As a strategy developer, I want the compiler to generate clean, modern strategy code, so that generated strategies are maintainable and follow current best practices.

#### Acceptance Criteria

1. WHEN generating strategy classes THEN the compiler SHALL use the enhanced Base import pattern
2. WHEN generating init() methods THEN indicator registrations SHALL be clearly organized
3. WHEN generating next() methods THEN trading logic SHALL be clean and readable
4. WHEN generating imports THEN only necessary imports SHALL be included
5. WHEN generating docstrings THEN strategy description and purpose SHALL be clearly documented

### Requirement 7: Backward Compatibility Preservation

**User Story:** As a system maintainer, I want the compiler to maintain compatibility with existing StrategySpec format, so that existing JSON specifications continue to work without modification.

#### Acceptance Criteria

1. WHEN processing existing StrategySpec JSON THEN the compiler SHALL parse all current fields correctly
2. WHEN entry_conditions are specified THEN they SHALL be converted to appropriate next() method logic
3. WHEN exit_conditions are specified THEN they SHALL be converted to appropriate next() method logic
4. WHEN optimization_params are specified THEN get_optimization_params() method SHALL be generated correctly
5. WHEN validate_params is needed THEN the method SHALL be generated with appropriate validation logic

### Requirement 8: Error Handling and Validation

**User Story:** As a strategy developer, I want the compiler to handle errors gracefully, so that invalid specifications produce clear error messages rather than broken code.

#### Acceptance Criteria

1. WHEN invalid indicator specifications are provided THEN the compiler SHALL raise descriptive errors
2. WHEN missing indicator functions are encountered THEN the Librarian system SHALL be invoked automatically
3. WHEN condition expressions are malformed THEN the compiler SHALL provide clear error messages
4. WHEN generated code has syntax errors THEN the compiler SHALL detect and report them
5. WHEN compilation fails THEN the error messages SHALL indicate the specific problem and location