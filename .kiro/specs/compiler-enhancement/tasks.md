# Implementation Plan: Compiler Enhancement

## Overview

This implementation plan transforms the research_agent/compiler.py from generating old-style `run()` methods to generating enhanced Base framework-compatible strategies with `init()` and `next()` methods. The approach focuses on incremental refactoring with comprehensive testing to ensure backward compatibility while modernizing the code generation patterns.

## Tasks

- [x] 1. Set up enhanced compiler foundation
  - [x] 1.1 Create backup of current compiler.py
    - Create backup file for rollback safety
    - _Requirements: 7.1_
  
  - [x] 1.2 Add enhanced Base framework imports and utilities
    - Update imports to include enhanced Base class
    - Add utility functions for code generation
    - _Requirements: 1.1, 6.1_
  
  - [x] 1.3 Write property test for enhanced Base inheritance
    - **Property 6: Enhanced Base inheritance**
    - **Validates: Requirements 1.1, 6.1**

- [x] 2. Implement indicator registration system
  - [x] 2.1 Create indicator registration generator
    - Implement `_generate_indicator_registrations()` function
    - Handle indicator parameter passing and function resolution
    - Support composite indicator patterns
    - _Requirements: 1.3, 2.1, 2.2, 2.3, 2.4_
  
  - [x] 2.2 Integrate with existing Librarian system
    - Ensure missing indicators trigger Librarian calls
    - Handle Librarian integration errors gracefully
    - _Requirements: 2.5, 8.2_
  
  - [x] 2.3 Write property test for indicator registration
    - **Property 2: Indicator registration transformation**
    - **Validates: Requirements 1.3, 2.1, 2.2, 2.3**
  
  - [x] 2.4 Write property test for composite indicator handling
    - **Property 10: Composite indicator handling**
    - **Validates: Requirements 2.4**

- [x] 3. Implement init() method generation
  - [x] 3.1 Create `_generate_init_method()` function
    - Generate clean init() method structure
    - Integrate indicator registrations
    - Add proper docstrings and organization
    - _Requirements: 1.2, 6.2, 6.5_
  
  - [x] 3.2 Write unit tests for init() method generation

    - Test various indicator combinations
    - Test empty indicator lists
    - Test complex indicator parameters
    - _Requirements: 1.2, 6.2_

- [x] 4. Implement condition expression transformation
  - [x] 4.1 Create expression transformer
    - Implement `_transform_condition_expressions()` function
    - Handle data access pattern transformations
    - Support historical data access with negative indexing
    - _Requirements: 1.5, 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 4.2 Add indicator reference resolution
    - Map indicator names to self.indicator_name[-1] patterns
    - Handle complex expression parsing
    - _Requirements: 3.4_
  
  - [x] 4.3 Write property test for data access transformation
    - **Property 3: Data access pattern transformation**
    - **Validates: Requirements 1.5, 3.1, 3.2, 3.3, 3.4, 3.5**

- [x] 5. Implement next() method generation
  - [x] 5.1 Create `_generate_next_method()` function
    - Generate next() method with trading logic
    - Integrate transformed condition expressions
    - Handle entry and exit logic separation
    - _Requirements: 1.2, 1.4, 4.1, 4.2, 7.2, 7.3_
  
  - [x] 5.2 Implement position management integration
    - Replace manual position tracking with self.buy()/self.sell()
    - Handle position sizing parameters
    - Remove manual position variables
    - _Requirements: 1.4, 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 5.3 Write property test for position management
    - **Property 4: Position management method usage**
    - **Validates: Requirements 1.4, 4.1, 4.2, 4.3, 4.4, 4.5**
  
  - [x] 5.4 Write property test for enhanced method generation
    - **Property 1: Enhanced framework method generation**
    - **Validates: Requirements 1.2, 7.2, 7.3**

- [x] 6. Checkpoint - Core functionality complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement time-based logic support
  - [x] 7.1 Add datetime_utils integration
    - Detect time-based conditions in expressions
    - Generate appropriate datetime_utils imports
    - Create timestamp access patterns
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 7.2 Implement time filtering generation
    - Generate market hours filtering code
    - Support custom time range conditions
    - Handle timestamp format conversion
    - _Requirements: 5.2, 5.3, 5.5_
  
  - [x] 7.3 Write property test for time-based logic
    - **Property 5: Time-based logic integration**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 8. Implement enhanced template system
  - [x] 8.1 Create new strategy class template
    - Design clean template structure for enhanced strategies
    - Integrate all generated components
    - Ensure proper code organization
    - _Requirements: 6.2, 6.4, 6.5_
  
  - [x] 8.2 Update main `compile_strategy()` function
    - Integrate all new generation functions
    - Replace old template with enhanced template
    - Maintain backward compatibility with StrategySpec
    - _Requirements: 7.1, 7.4, 7.5_
  
  - [x] 8.3 Write property test for code organization
    - **Property 9: Code organization and imports**
    - **Validates: Requirements 6.2, 6.4, 6.5**

- [x] 9. Implement comprehensive error handling
  - [x] 9.1 Add validation framework
    - Implement pre-compilation StrategySpec validation
    - Add post-compilation syntax validation
    - Create descriptive error messages
    - _Requirements: 8.1, 8.3, 8.4, 8.5_
  
  - [x] 9.2 Enhance Librarian integration error handling
    - Handle Librarian failures gracefully
    - Provide clear error messages for missing indicators
    - Implement retry logic for Librarian calls
    - _Requirements: 2.5, 8.2_
  
  - [x] 9.3 Write property test for error handling
    - **Property 8: Comprehensive error handling**
    - **Validates: Requirements 2.5, 8.1, 8.2, 8.3, 8.4, 8.5**

- [x] 10. Implement backward compatibility preservation
  - [x] 10.1 Add compatibility layer for existing specs
    - Ensure all existing StrategySpec fields are handled
    - Maintain equivalent functionality with new patterns
    - Test with existing strategy specifications
    - _Requirements: 7.1, 7.4, 7.5_
  
  - [x] 10.2 Write property test for backward compatibility
    - **Property 7: Backward compatibility preservation**
    - **Validates: Requirements 7.1, 7.4, 7.5**
  
  - [x] 10.3 Write integration tests with existing specs
    - Test compilation of existing RSI strategy specs
    - Test complex multi-indicator strategy specs
    - Test optimization parameter generation
    - _Requirements: 7.1, 7.4, 7.5_

- [x] 11. Final integration and testing
  - [x] 11.1 Update import optimization
    - Implement smart import generation
    - Remove unused imports from generated code
    - Ensure all necessary imports are included
    - _Requirements: 6.4_
  
  - [x] 11.2 Add comprehensive syntax validation
    - Validate generated code compiles correctly
    - Test generated strategies execute with enhanced Base
    - Verify equivalent results to manual strategies
    - _Requirements: 8.4_
  
  - [x] 11.3 Write end-to-end integration tests
    - Test complete compilation pipeline
    - Test generated strategies with backtesting engine
    - Test optimization parameter usage
    - _Requirements: 7.1, 7.4, 7.5_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests ensure compatibility with existing system components