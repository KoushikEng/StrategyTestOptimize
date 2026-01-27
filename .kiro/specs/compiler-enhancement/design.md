# Design Document

## Overview

The compiler enhancement will modernize the research_agent/compiler.py to generate strategies compatible with the enhanced Base framework. The design transforms the current template-based approach from generating old-style `run()` methods to generating clean `init()` and `next()` methods that leverage built-in position management, indicator registration, and data access patterns.

The core transformation involves:
- Replacing manual loop-based `run()` methods with `init()` and `next()` patterns
- Converting direct indicator calculations to `self.I()` registrations
- Updating data access from array indexing to `self.data` patterns
- Eliminating manual position tracking in favor of built-in `self.buy()`/`self.sell()`
- Adding support for time-based filtering using datetime_utils

## Architecture

### Current Architecture Issues

The existing compiler generates strategies with these problematic patterns:
```python
def run(self, data, **kwargs):
    symbol, dates, times, opens, highs, lows, closes, volume = data
    # Manual indicator calculations
    sma = calculate_sma(closes, 20)
    # Manual position tracking
    in_position = False
    entry_price = 0.0
    # Manual loop with array indexing
    for i in range(start_idx, n):
        if not in_position and condition:
            in_position = True
            entry_price = closes[i]
```

### Enhanced Architecture Design

The new compiler will generate strategies with these modern patterns:
```python
def init(self):
    # Indicator registration
    self.sma = self.I(calculate_sma, self.data.Close, 20)

def next(self):
    # Clean condition checking with data accessors
    if self.sma[-1] > self.data.Close[-1] and not self.position:
        self.buy()
    elif self.position and exit_condition:
        self.sell()
```

### Component Relationships

```mermaid
graph TD
    A[StrategySpec JSON] --> B[Enhanced Compiler]
    B --> C[Template Engine]
    C --> D[Init Method Generator]
    C --> E[Next Method Generator]
    C --> F[Import Generator]
    
    D --> G[Indicator Registration]
    E --> H[Trading Logic]
    E --> I[Data Access Patterns]
    
    G --> J[self.I() calls]
    H --> K[self.buy()/self.sell()]
    I --> L[self.data.Close[-1]]
    
    B --> M[Generated Strategy Class]
    M --> N[Enhanced Base Framework]
```

## Components and Interfaces

### Enhanced Compiler Module

**Core Functions:**
- `compile_strategy(spec: StrategySpec) -> str`: Main compilation function
- `_generate_init_method(indicators: List[Indicator]) -> str`: Generate init() method
- `_generate_next_method(entry_conditions, exit_conditions) -> str`: Generate next() method
- `_generate_indicator_registrations(indicators) -> str`: Generate self.I() calls
- `_generate_enhanced_imports(indicators) -> str`: Generate necessary imports

**Key Interfaces:**
```python
class EnhancedCompiler:
    def compile_strategy(self, spec: StrategySpec) -> str:
        """Compile StrategySpec to enhanced Base-compatible code."""
        
    def _generate_init_method(self, indicators: List[Indicator]) -> str:
        """Generate init() method with indicator registrations."""
        
    def _generate_next_method(self, entry_conditions: List[Condition], 
                            exit_conditions: List[Condition]) -> str:
        """Generate next() method with trading logic."""
```

### Template System Redesign

**Init Method Template:**
```python
def init(self):
    """Initialize strategy indicators and parameters."""
    # Generated indicator registrations
    {indicator_registrations}
```

**Next Method Template:**
```python
def next(self):
    """Process the current bar."""
    # Time-based filtering (if needed)
    {time_filters}
    
    # Entry logic
    if not self.position and ({entry_logic}):
        self.buy({position_size})
    
    # Exit logic
    elif self.position and ({exit_logic}):
        self.sell()
```

### Indicator Registration Generator

**Function:** `_generate_indicator_registrations(indicators: List[Indicator]) -> str`

**Logic:**
1. For each indicator in the specification:
   - Resolve indicator function name using existing `get_indicator_function_name()`
   - Generate `self.I()` call with appropriate parameters
   - Handle composite indicators (multiple return values)
   - Store indicator reference for use in conditions

**Example Output:**
```python
self.rsi = self.I(calculate_rsi, self.data.Close, period=14)
self.sma_fast = self.I(calculate_sma, self.data.Close, 10)
self.sma_slow = self.I(calculate_sma, self.data.Close, 20)
```

### Condition Expression Transformer

**Function:** `_transform_condition_expressions(conditions: List[Condition]) -> str`

**Transformations:**
- Replace indicator names with `self.indicator_name[-1]`
- Replace data references with `self.data.Close[-1]`, `self.data.Volume[-1]`, etc.
- Handle historical data access with negative indexing
- Add time-based condition support

**Example Transformations:**
```python
# Input: "rsi < 30"
# Output: "self.rsi[-1] < 30"

# Input: "closes > sma_20"
# Output: "self.data.Close[-1] > self.sma_20[-1]"

# Input: "volume > volume[1] * 1.5"
# Output: "self.data.Volume[-1] > self.data.Volume[-2] * 1.5"
```

### Time-Based Logic Integration

**Function:** `_generate_time_filters(conditions: List[Condition]) -> str`

**Capabilities:**
- Detect time-based conditions in expressions
- Generate appropriate datetime_utils imports
- Create timestamp access patterns
- Handle market hours, opening/closing hour filters

**Example Output:**
```python
# If time-based conditions detected
current_timestamp = int(self.data.timestamps[-1])
if not is_market_hours(current_timestamp):
    return  # Skip trading outside market hours
```

## Data Models

### Enhanced Strategy Template Structure

```python
class {StrategyName}(Base):
    """
    {description}
    Generated by Enhanced Compiler
    """
    
    def init(self):
        """Initialize strategy indicators and parameters."""
        {indicator_registrations}
    
    def next(self):
        """Process the current bar."""
        {time_based_filters}
        
        # Entry conditions
        if not self.position and ({entry_logic}):
            self.buy({position_size})
        
        # Exit conditions  
        elif self.position and ({exit_logic}):
            self.sell()
    
    def validate_params(self, **kwargs) -> bool:
        {validation_logic}
        return True
    
    @staticmethod
    def get_optimization_params():
        {optimization_params}
```

### Indicator Registration Data Model

```python
@dataclass
class IndicatorRegistration:
    name: str              # Variable name (e.g., "rsi")
    function_name: str     # Function name (e.g., "calculate_rsi")
    data_source: str       # Data source (e.g., "self.data.Close")
    parameters: Dict[str, Any]  # Parameters (e.g., {"period": 14})
    
    def generate_code(self) -> str:
        """Generate self.I() registration code."""
        params = ", ".join([f"{k}={v}" for k, v in self.parameters.items()])
        return f"self.{self.name} = self.I({self.function_name}, {self.data_source}, {params})"
```

### Condition Expression Data Model

```python
@dataclass
class TransformedCondition:
    original_expression: str
    transformed_expression: str
    required_indicators: List[str]
    uses_time_logic: bool
    
    def generate_code(self) -> str:
        """Generate condition code for next() method."""
        return self.transformed_expression
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Now I need to analyze the acceptance criteria to determine which ones are testable as properties. Let me use the prework tool:

### Property Reflection

After analyzing the acceptance criteria, I identified several areas where properties can be consolidated:
- Indicator registration properties can be combined into comprehensive indicator handling
- Data access patterns can be unified into a single transformation property
- Position management properties can be combined into trading method usage
- Time-based properties can be consolidated into time logic handling
- Error handling properties can be unified into comprehensive error management

### Correctness Properties

Property 1: Enhanced framework method generation
*For any* valid StrategySpec, the generated strategy code should contain init() and next() methods and should not contain a run() method with manual loops
**Validates: Requirements 1.2, 7.2, 7.3**

Property 2: Indicator registration transformation
*For any* StrategySpec with indicators, each indicator should be registered using self.I() calls in the init() method, with correct function names and parameters
**Validates: Requirements 1.3, 2.1, 2.2, 2.3**

Property 3: Data access pattern transformation
*For any* condition expression containing data references, the generated code should use self.data.Close[-1], self.data.Volume[-1] patterns instead of array indexing
**Validates: Requirements 1.5, 3.1, 3.2, 3.3, 3.4, 3.5**

Property 4: Position management method usage
*For any* StrategySpec with entry and exit conditions, the generated next() method should use self.buy() and self.sell() calls instead of manual position tracking variables
**Validates: Requirements 1.4, 4.1, 4.2, 4.3, 4.4, 4.5**

Property 5: Time-based logic integration
*For any* StrategySpec with time-based conditions, the generated code should import datetime_utils functions and use appropriate time filtering with self.data.timestamps[-1]
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

Property 6: Enhanced Base inheritance
*For any* generated strategy, the code should inherit from the enhanced Base class with correct import statements
**Validates: Requirements 1.1, 6.1**

Property 7: Backward compatibility preservation
*For any* existing valid StrategySpec JSON, the enhanced compiler should parse all fields correctly and generate equivalent functionality using the new patterns
**Validates: Requirements 7.1, 7.4, 7.5**

Property 8: Comprehensive error handling
*For any* invalid StrategySpec or compilation error, the compiler should raise descriptive exceptions with specific problem details and trigger appropriate system responses (like Librarian calls)
**Validates: Requirements 2.5, 8.1, 8.2, 8.3, 8.4, 8.5**

Property 9: Code organization and imports
*For any* generated strategy, the code should have well-organized init() methods, include only necessary imports, and contain appropriate docstrings with strategy descriptions
**Validates: Requirements 6.2, 6.4, 6.5**

Property 10: Composite indicator handling
*For any* indicator that returns multiple values, the generated code should handle composite indicator access patterns correctly
**Validates: Requirements 2.4**

## Error Handling

### Compilation Error Management

**Error Categories:**
1. **Invalid StrategySpec**: Malformed JSON, missing required fields, invalid field values
2. **Missing Indicators**: Indicator functions not found in calculate.indicators
3. **Expression Errors**: Malformed condition expressions, invalid syntax
4. **Template Errors**: Code generation failures, syntax errors in generated code

**Error Handling Strategy:**
- Validate StrategySpec before compilation begins
- Use descriptive error messages with specific problem locations
- Integrate with Librarian system for missing indicators
- Perform syntax validation on generated code
- Provide fallback patterns for edge cases

**Example Error Handling:**
```python
def compile_strategy(spec: StrategySpec) -> str:
    try:
        # Validate spec
        _validate_strategy_spec(spec)
        
        # Generate code sections
        init_method = _generate_init_method(spec.indicators)
        next_method = _generate_next_method(spec.entry_conditions, spec.exit_conditions)
        
        # Validate generated code syntax
        _validate_generated_syntax(generated_code)
        
        return generated_code
        
    except IndicatorNotFoundError as e:
        # Trigger Librarian system
        logger.info(f"Invoking Librarian for missing indicator: {e.indicator_name}")
        add_indicator(e.indicator_name)
        return compile_strategy(spec)  # Retry after Librarian
        
    except ExpressionError as e:
        raise CompilationError(f"Invalid condition expression '{e.expression}': {e.details}")
        
    except SyntaxError as e:
        raise CompilationError(f"Generated code has syntax error at line {e.lineno}: {e.msg}")
```

### Validation Framework

**Pre-compilation Validation:**
- StrategySpec field validation using Pydantic
- Indicator specification validation
- Condition expression syntax checking
- Parameter type validation

**Post-compilation Validation:**
- Generated code syntax validation
- Import statement verification
- Method signature validation
- Docstring presence validation

## Testing Strategy

### Dual Testing Approach

The testing strategy combines unit tests for specific examples and edge cases with property-based tests for comprehensive validation across all possible inputs.

**Unit Testing Focus:**
- Specific StrategySpec examples with known expected outputs
- Edge cases like empty indicator lists, complex expressions
- Error conditions with invalid inputs
- Integration with existing Librarian system
- Backward compatibility with existing strategy specifications

**Property-Based Testing Focus:**
- Universal properties that hold for all valid StrategySpec inputs
- Code generation patterns across randomized specifications
- Expression transformation correctness across varied conditions
- Import optimization across different indicator combinations
- Error handling consistency across malformed inputs

### Property-Based Test Configuration

**Testing Library:** Use Hypothesis for Python property-based testing
**Test Configuration:** Minimum 100 iterations per property test
**Test Tagging:** Each property test references its design document property

**Example Property Test Structure:**
```python
from hypothesis import given, strategies as st
import pytest

@given(st.builds(StrategySpec, 
                indicators=st.lists(st.builds(Indicator), min_size=1),
                entry_conditions=st.lists(st.builds(Condition), min_size=1)))
def test_indicator_registration_property(spec):
    """
    Feature: compiler-enhancement, Property 2: Indicator registration transformation
    For any StrategySpec with indicators, each indicator should be registered 
    using self.I() calls in the init() method.
    """
    generated_code = compile_strategy(spec)
    
    # Verify init() method contains self.I() calls
    assert "def init(self):" in generated_code
    
    # Verify each indicator has a self.I() registration
    for indicator in spec.indicators:
        expected_pattern = f"self.{indicator.name} = self.I("
        assert expected_pattern in generated_code
        
    # Verify no manual indicator calculations
    assert "calculate_" not in generated_code.split("def init(self):")[1].split("def next(self):")[0]
```

**Unit Test Examples:**
- Test specific RSI strategy compilation
- Test strategy with multiple indicators and complex conditions
- Test error handling with missing indicator functions
- Test backward compatibility with existing JSON specifications
- Test time-based strategy compilation with datetime_utils integration

**Integration Testing:**
- Test generated strategies execute correctly with enhanced Base framework
- Test compiled strategies produce equivalent results to manually written strategies
- Test optimization parameter generation and usage
- Test Librarian integration during compilation process

The comprehensive testing approach ensures both correctness of individual transformations and overall system reliability across all possible strategy specifications.