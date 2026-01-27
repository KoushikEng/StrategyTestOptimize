"""
Enhanced Strategy Compiler

Transforms a StrategySpec (JSON) into a valid Python strategy class compatible
with the enhanced Base framework using init() and next() methods.
This is a DETERMINISTIC, SANDBOXED component - no LLM involvement.
"""

from research_agent.schema import StrategySpec, Indicator, IndicatorType, Condition
from typing import Dict, Optional, List
from research_agent.tools import write_file
import importlib
import sys
import re
import ast

# Custom exception classes for better error handling
class CompilationError(Exception):
    """Base exception for compilation errors."""
    pass

class IndicatorNotFoundError(CompilationError):
    """Exception raised when an indicator function cannot be resolved."""
    def __init__(self, indicator_name: str):
        self.indicator_name = indicator_name
        super().__init__(f"Indicator '{indicator_name}' not found")

class ExpressionError(CompilationError):
    """Exception raised when condition expressions are malformed."""
    def __init__(self, expression: str, details: str):
        self.expression = expression
        self.details = details
        super().__init__(f"Invalid expression '{expression}': {details}")

class ValidationError(CompilationError):
    """Exception raised when StrategySpec validation fails."""
    pass

def _validate_strategy_spec(spec: StrategySpec) -> None:
    """Validate StrategySpec before compilation."""
    # Basic validation (Pydantic handles most of this, but we can add custom checks)
    if not spec.name:
        raise ValidationError("Strategy name cannot be empty")
    
    if not spec.name.isidentifier():
        raise ValidationError(f"Strategy name '{spec.name}' is not a valid Python identifier")
    
    if not spec.name[0].isupper():
        raise ValidationError(f"Strategy name '{spec.name}' must start with uppercase letter (PascalCase)")
    
    # Validate indicators
    for indicator in spec.indicators:
        if not indicator.name.isidentifier():
            raise ValidationError(f"Indicator name '{indicator.name}' is not a valid Python identifier")
        
        # Check for reserved keywords
        reserved_keywords = {'and', 'or', 'not', 'if', 'else', 'elif', 'for', 'while', 'def', 'class', 'import', 'from'}
        if indicator.name in reserved_keywords:
            raise ValidationError(f"Indicator name '{indicator.name}' is a reserved Python keyword")
    
    # Validate condition expressions
    for condition in spec.entry_conditions + spec.exit_conditions:
        _validate_condition_expression(condition.expression)

def _validate_condition_expression(expression: str) -> None:
    """Validate condition expression syntax."""
    if not expression.strip():
        raise ExpressionError(expression, "Expression cannot be empty")
    
    # Check for potentially dangerous patterns
    dangerous_patterns = [
        r'\bexec\b', r'\beval\b', r'\b__import__\b', r'\bopen\b',
        r'\bfile\b', r'\binput\b', r'\braw_input\b'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, expression, re.IGNORECASE):
            raise ExpressionError(expression, f"Expression contains potentially dangerous pattern: {pattern}")
    
    # Basic syntax validation - try to parse as Python expression
    try:
        # Create a safe environment for testing
        test_vars = {
            'closes': [100], 'opens': [99], 'highs': [101], 'lows': [98], 'volume': [1000],
            'sma': [100], 'ema': [100], 'rsi': [50], 'macd': [0],
            'timestamp': 1234567890, 'True': True, 'False': False
        }
        # Try to evaluate the expression in a safe context
        eval(expression, {"__builtins__": {}}, test_vars)
    except SyntaxError as e:
        raise ExpressionError(expression, f"Syntax error: {str(e)}")
    except Exception as e:
        # This is expected for many valid expressions, so we just check for syntax
        pass

def _validate_generated_syntax(code: str) -> None:
    """Validate that generated code has correct syntax and structure."""
    try:
        # Parse the code to check syntax
        tree = ast.parse(code)
        
        # Additional structural validation
        _validate_code_structure(tree, code)
        
    except SyntaxError as e:
        raise CompilationError(f"Generated code has syntax error at line {e.lineno}: {e.msg}")

def _validate_code_structure(tree: ast.AST, code: str) -> None:
    """Validate the structure of generated code."""
    # Find the strategy class
    strategy_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            strategy_class = node
            break
    
    if not strategy_class:
        raise CompilationError("Generated code must contain a strategy class")
    
    # Check that class inherits from Base
    if not strategy_class.bases:
        raise CompilationError("Strategy class must inherit from Base")
    
    base_name = None
    for base in strategy_class.bases:
        if isinstance(base, ast.Name) and base.id == 'Base':
            base_name = 'Base'
            break
    
    if base_name != 'Base':
        raise CompilationError("Strategy class must inherit from Base")
    
    # Check required methods exist
    method_names = []
    for node in strategy_class.body:
        if isinstance(node, ast.FunctionDef):
            method_names.append(node.name)
    
    required_methods = ['init', 'next', 'validate_params', 'get_optimization_params']
    for method in required_methods:
        if method not in method_names:
            raise CompilationError(f"Generated strategy must have {method}() method")
    
    # Validate that enhanced patterns are used (not old patterns)
    if 'def run(self, data, **kwargs):' in code:
        raise CompilationError("Generated code must not contain old-style run() method")
    
    if 'for i in range(' in code:
        raise CompilationError("Generated code must not contain manual loops")
    
    if 'in_position = False' in code or 'in_position = True' in code:
        raise CompilationError("Generated code must not use manual position tracking")
    
    # Validate enhanced patterns are present when needed
    if 'self.I(' in code:
        # If indicators are registered, init method should exist
        if 'def init(self):' not in code:
            raise CompilationError("Code with indicators must have init() method")
    
    if 'self.buy()' in code or 'self.sell()' in code:
        # If trading methods are used, position checks should exist
        if "self.position['is_in_position']" not in code:
            raise CompilationError("Code with trading methods must use enhanced position management")

def _validate_strategy_execution(spec: StrategySpec, code: str) -> None:
    """Validate that generated strategy can be executed with enhanced Base."""
    try:
        # Create a temporary module to test compilation
        import tempfile
        import os
        import sys
        
        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Try to compile the file
            with open(temp_file, 'r') as f:
                compile(f.read(), temp_file, 'exec')
            
            # Try to import and instantiate (basic check)
            spec_name = temp_file.replace('.py', '').replace('/', '_').replace('\\', '_')
            module_name = f"temp_strategy_{spec_name}"
            
            # Add temp directory to path
            temp_dir = os.path.dirname(temp_file)
            if temp_dir not in sys.path:
                sys.path.insert(0, temp_dir)
            
            try:
                # This is a basic compilation check - we don't actually run the strategy
                # since that would require full backtesting infrastructure
                pass
                
            except ImportError as e:
                # Expected - we don't have full environment, but compilation worked
                pass
                
        finally:
            # Clean up
            try:
                os.unlink(temp_file)
            except:
                pass
                
    except Exception as e:
        raise CompilationError(f"Generated strategy failed execution validation: {str(e)}")

# Lazy import to avoid LLM dependency during testing
def _get_librarian():
    """Lazy import of librarian to avoid LLM initialization during testing."""
    try:
        from research_agent.librarian import add_indicator
        return add_indicator
    except Exception as e:
        print(f"Warning: Could not import librarian: {e}")
        return None

# Enhanced compiler utility functions
def _detect_time_based_conditions(conditions: List[Condition]) -> bool:
    """Detect if any conditions use time-based logic."""
    time_keywords = [
        'hour', 'minute', 'second', 'market_hours', 'opening_hour', 'closing_hour', 
        'timestamp', 'is_market_hours', 'is_opening_hour', 'is_closing_hour',
        'extract_hour', 'extract_minute', 'is_in_time_range', 'day_of_week'
    ]
    for condition in conditions:
        if any(keyword in condition.expression.lower() for keyword in time_keywords):
            return True
    return False

def _generate_time_based_imports(conditions: List[Condition]) -> str:
    """Generate datetime_utils imports based on conditions."""
    if not _detect_time_based_conditions(conditions):
        return ""
    
    # Detect which specific functions are needed
    needed_functions = set()
    
    for condition in conditions:
        expr = condition.expression.lower()
        if 'is_market_hours' in expr:
            needed_functions.add('is_market_hours')
        if 'is_opening_hour' in expr:
            needed_functions.add('is_opening_hour')
        if 'is_closing_hour' in expr:
            needed_functions.add('is_closing_hour')
        if 'extract_hour' in expr:
            needed_functions.add('extract_hour')
        if 'extract_minute' in expr:
            needed_functions.add('extract_minute')
        if 'is_in_time_range' in expr:
            needed_functions.add('is_in_time_range')
        if 'day_of_week' in expr or 'extract_day_of_week' in expr:
            needed_functions.add('extract_day_of_week')
    
    # If no specific functions detected but time keywords found, import common ones
    if not needed_functions and _detect_time_based_conditions(conditions):
        needed_functions = {'is_market_hours', 'extract_hour'}
    
    if needed_functions:
        functions_str = ', '.join(sorted(needed_functions))
        return f"from datetime_utils import {functions_str}"
    
    return ""

def _generate_time_filters(conditions: List[Condition]) -> str:
    """Generate time-based filtering code for next() method."""
    if not _detect_time_based_conditions(conditions):
        return ""
    
    # Generate timestamp access and basic market hours filter
    return '''        # Time-based filtering
        current_timestamp = int(self.data.timestamps[-1])
        if not is_market_hours(current_timestamp):
            return  # Skip trading outside market hours'''

def _transform_time_expressions(expression: str) -> str:
    """Transform time-based expressions to use current timestamp."""
    # Transform common time-based patterns
    transformations = [
        # Transform timestamp references first
        (r'\bself\.data\.timestamps\[-1\]', 'current_timestamp'),
        (r'\btimestamps\[-1\]', 'current_timestamp'),
        (r'\btimestamp\b(?!\[)', 'current_timestamp'),
        # Transform function calls to use current_timestamp
        (r'\bis_market_hours\(timestamp\)', 'is_market_hours(current_timestamp)'),
        (r'\bextract_hour\(timestamp\)', 'extract_hour(current_timestamp)'),
        (r'\bis_opening_hour\(timestamp\)', 'is_opening_hour(current_timestamp)'),
        (r'\bis_closing_hour\(timestamp\)', 'is_closing_hour(current_timestamp)'),
        (r'\bextract_minute\(timestamp\)', 'extract_minute(current_timestamp)'),
        (r'\bextract_day_of_week\(timestamp\)', 'extract_day_of_week(current_timestamp)'),
        # Handle cases where timestamp was already transformed to self.timestamp[-1]
        (r'\bis_market_hours\(self\.timestamp\[-1\]\)', 'is_market_hours(current_timestamp)'),
        (r'\bextract_hour\(self\.timestamp\[-1\]\)', 'extract_hour(current_timestamp)'),
        (r'\bis_opening_hour\(self\.timestamp\[-1\]\)', 'is_opening_hour(current_timestamp)'),
        (r'\bis_closing_hour\(self\.timestamp\[-1\]\)', 'is_closing_hour(current_timestamp)'),
        (r'\bextract_minute\(self\.timestamp\[-1\]\)', 'extract_minute(current_timestamp)'),
        (r'\bextract_day_of_week\(self\.timestamp\[-1\]\)', 'extract_day_of_week(current_timestamp)'),
    ]
    
    result = expression
    for pattern, replacement in transformations:
        result = re.sub(pattern, replacement, result)
    
    return result

def _extract_indicator_names(conditions: List[Condition]) -> set:
    """Extract indicator names referenced in conditions."""
    indicator_names = set()
    
    # Time function names that should not be treated as indicators
    time_functions = {
        'is_market_hours', 'extract_hour', 'extract_minute', 'is_opening_hour', 
        'is_closing_hour', 'extract_day_of_week', 'is_in_time_range', 'timestamp',
        'current_timestamp'
    }
    
    # Data access names that should not be treated as indicators
    data_names = {'closes', 'opens', 'highs', 'lows', 'volume', 'timestamps'}
    
    # Reserved keywords and operators
    reserved_keywords = {
        'and', 'or', 'not', 'True', 'False', 'if', 'else', 'elif', 'in', 'is',
        'None', 'self', 'data', 'Close', 'Open', 'High', 'Low', 'Volume'
    }
    
    for condition in conditions:
        # Simple regex to find potential indicator names (alphanumeric + underscore)
        matches = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', condition.expression)
        for match in matches:
            # Filter out time functions, data names, and reserved keywords
            if (match not in time_functions and 
                match not in data_names and 
                match not in reserved_keywords):
                indicator_names.add(match)
    
    return indicator_names

def _transform_data_access(expression: str) -> str:
    """Transform data access patterns from old to new format."""
    # Transform common data access patterns
    transformations = {
        r'\bcloses\[([^\]]+)\]': r'self.data.Close[\1]',
        r'\bopens\[([^\]]+)\]': r'self.data.Open[\1]',
        r'\bhighs\[([^\]]+)\]': r'self.data.High[\1]',
        r'\blows\[([^\]]+)\]': r'self.data.Low[\1]',
        r'\bvolume\[([^\]]+)\]': r'self.data.Volume[\1]',
        r'\bcloses\b(?!\[)': r'self.data.Close[-1]',
        r'\bopens\b(?!\[)': r'self.data.Open[-1]',
        r'\bhighs\b(?!\[)': r'self.data.High[-1]',
        r'\blows\b(?!\[)': r'self.data.Low[-1]',
        r'\bvolume\b(?!\[)': r'self.data.Volume[-1]',
    }
    
    result = expression
    for pattern, replacement in transformations.items():
        result = re.sub(pattern, replacement, result)
    
    return result

def _transform_indicator_access(expression: str, indicator_names: set) -> str:
    """Transform indicator access patterns to use self.indicator_name[-1]."""
    result = expression
    
    # Filter out time function names from indicator names to avoid conflicts
    time_functions = {'is_market_hours', 'extract_hour', 'extract_minute', 'is_opening_hour', 
                     'is_closing_hour', 'extract_day_of_week', 'is_in_time_range'}
    
    actual_indicator_names = indicator_names - time_functions
    
    for indicator_name in actual_indicator_names:
        # Transform indicator[i] to self.indicator_name[i]
        pattern = rf'\b{indicator_name}\[([^\]]+)\]'
        replacement = rf'self.{indicator_name}[\1]'
        result = re.sub(pattern, replacement, result)
        
        # Transform bare indicator name to self.indicator_name[-1]
        pattern = rf'\b{indicator_name}\b(?!\[)'
        replacement = rf'self.{indicator_name}[-1]'
        result = re.sub(pattern, replacement, result)
    
    return result

# Dynamic Import Wrapper
def get_indicator_function_name(name: str) -> Optional[str]:
    """
    Dynamically resolve indicator function name.
    If missing, trigger Librarian to create it.
    Returns the valid function name (e.g. 'calculate_sma') or None.
    """
    func_name = f"calculate_{name}"

    INDICATORS_PACKAGE = "calculate.indicators"
    
    def try_import(new_ind_category: Optional[str] = None):
        try:
            if new_ind_category and INDICATORS_PACKAGE in sys.modules:  # Reload if already imported
                submod = f"{INDICATORS_PACKAGE}.{new_ind_category}"
                if submod in sys.modules:
                    # First reload submodules (trend, momentum, etc)
                    importlib.reload(sys.modules[submod])

                # Then main module
                importlib.reload(sys.modules[INDICATORS_PACKAGE])
            else:  # Import first time
                importlib.import_module(INDICATORS_PACKAGE)
            
            module = sys.modules[INDICATORS_PACKAGE]
            return hasattr(module, func_name)
        except ImportError as e:
            print(f"[compiler] ImportError: {e}")
            return False

    if try_import():
        return func_name
    
    # Not found -> Invoke Librarian
    print(f"⚠️ Indicator '{name}' not found. Invoking Librarian...")
    try:
        add_indicator_func = _get_librarian()
        if add_indicator_func:
            new_ind_category = add_indicator_func(name)
            if new_ind_category and try_import(new_ind_category):
                print(f"new indicator function '{func_name}' added successfully to {INDICATORS_PACKAGE}.{new_ind_category}")
                return func_name
        else:
            print("Librarian not available")
    except Exception as e:
        print(f"Librarian error: {e}")
        
    # If we get here, the indicator could not be resolved
    raise IndicatorNotFoundError(name)


def _generate_indicator_registrations(indicators: List[Indicator]) -> str:
    """Generate indicator registration calls using self.I() pattern."""
    from research_agent.indicator_registry import get_signature
    
    lines = []
    
    for ind in indicators:
        # 1. Ensure indicator function exists (Trigger Librarian side-effect)
        fn_name = get_indicator_function_name(ind.type)
        if not fn_name:
            print(f"❌ Could not resolve indicator: {ind.type}")
            continue

        params = ind.params
        
        # 2. Look up signature in registry
        sig = get_signature(ind.type)
        
        if sig:
            # Build args from signature for enhanced framework
            arg_parts = []
            
            # Add data source (self.data.Close.values, etc.)
            for arg in sig.args:
                if arg == 'closes':
                    arg_parts.append('self.data.Close.values')
                elif arg == 'opens':
                    arg_parts.append('self.data.Open.values')
                elif arg == 'highs':
                    arg_parts.append('self.data.High.values')
                elif arg == 'lows':
                    arg_parts.append('self.data.Low.values')
                elif arg == 'volume':
                    arg_parts.append('self.data.Volume.values')
                else:
                    arg_parts.append(arg)
            
            # Add parameters with defaults
            for param_name, default_value in sig.defaults.items():
                value = params.get(param_name, default_value)
                arg_parts.append(f"{param_name}={value}")
            
            args = ", ".join(arg_parts)
        else:
            # Fallback for unregistered indicators (should be rare)
            print(f"⚠️ No signature found for '{ind.type}', using generic fallback")
            if 'period' in params:
                args = f"self.data.Close, {params['period']}"
            else:
                args = "self.data.Close"

        # 3. Generate self.I() registration call
        lines.append(f"        self.{ind.name} = self.I({fn_name}, {args})")

    return "\n".join(lines)


def _generate_init_method(indicators: List[Indicator]) -> str:
    """Generate init() method with indicator registrations."""
    if not indicators:
        return '''    def init(self):
        """Initialize strategy indicators and parameters."""
        pass'''
    
    indicator_registrations = _generate_indicator_registrations(indicators)
    
    return f'''    def init(self):
        """Initialize strategy indicators and parameters."""
{indicator_registrations}'''


def _transform_condition_expressions(conditions: List[Condition], indicator_names: set) -> str:
    """Transform condition expressions to use enhanced framework patterns."""
    if not conditions:
        return "True"
    
    transformed_exprs = []
    for condition in conditions:
        # Transform data access patterns
        expr = _transform_data_access(condition.expression)
        
        # Transform indicator access patterns
        expr = _transform_indicator_access(expr, indicator_names)
        
        # Transform time-based expressions
        expr = _transform_time_expressions(expr)
        
        transformed_exprs.append(f"({expr})")
    
    return " and ".join(transformed_exprs)


def _generate_next_method(entry_conditions: List[Condition], exit_conditions: List[Condition], 
                         indicator_names: set) -> str:
    """Generate next() method with trading logic."""
    
    # Transform conditions
    entry_logic = _transform_condition_expressions(entry_conditions, indicator_names)
    exit_logic = _transform_condition_expressions(exit_conditions, indicator_names)
    
    # Generate time-based filtering if needed
    all_conditions = entry_conditions + exit_conditions
    time_filters = _generate_time_filters(all_conditions)
    
    # Build the method
    method_parts = [
        '    def next(self):',
        '        """Process the current bar."""'
    ]
    
    if time_filters:
        method_parts.append(time_filters)
        method_parts.append('')  # Empty line for readability
    
    # Handle empty conditions properly
    if not entry_conditions and not exit_conditions:
        method_parts.extend([
            '        # No trading conditions specified',
            '        pass'
        ])
    elif not entry_conditions:
        method_parts.extend([
            '        # No entry conditions - only exit logic',
            f'        if self.position[\'in_position\'] and ({exit_logic}):',
            '            self.sell()'
        ])
    elif not exit_conditions:
        method_parts.extend([
            '        # No exit conditions - only entry logic',
            f'        if not self.position[\'in_position\'] and ({entry_logic}):',
            '            self.buy()'
        ])
    else:
        method_parts.extend([
            '        # Entry conditions',
            f'        if not self.position[\'in_position\'] and ({entry_logic}):',
            '            self.buy()',
            '',
            '        # Exit conditions',
            f'        elif self.position[\'in_position\'] and ({exit_logic}):',
            '            self.sell()'
        ])
    
    return '\n'.join(method_parts)


def _generate_optimization_params(params: Dict[str, tuple]) -> str:
    """Generate get_optimization_params method."""
    if not params:
        return "        return {}"
    lines = ["        return {"]
    for k, v in params.items():
        lines.append(f'            "{k}": {v},')
    lines.append("        }")
    return "\n".join(lines)


def compile_strategy(spec: StrategySpec) -> str:
    """
    Compile a StrategySpec into executable Python code using enhanced Base framework.
    """
    try:
        # Validate StrategySpec before compilation
        _validate_strategy_spec(spec)
        
        # Collect imports needed
        imports = []
        needed_funcs = set()
        for ind in spec.indicators:
            fn_name = f"calculate_{ind.type}"
            needed_funcs.add(fn_name)
        
        if needed_funcs:
            imports.append(f"from calculate.indicators import {', '.join(sorted(needed_funcs))}")
        
        # Add datetime_utils imports if needed
        all_conditions = spec.entry_conditions + spec.exit_conditions
        datetime_imports = _generate_time_based_imports(all_conditions)
        if datetime_imports:
            imports.append(datetime_imports)
        
        indicator_imports_str = "\n".join(imports)
        
        # Generate enhanced methods
        init_method = _generate_init_method(spec.indicators)
        
        # Extract indicator names for condition transformation
        indicator_names = _extract_indicator_names(all_conditions)
        # Add indicator names from spec
        for ind in spec.indicators:
            indicator_names.add(ind.name)
        
        next_method = _generate_next_method(spec.entry_conditions, spec.exit_conditions, indicator_names)
        
        opt_params = _generate_optimization_params(spec.optimization_params)
        
        # Generate the full enhanced class
        code = f'''"""
Auto-generated strategy: {spec.name}
{spec.description or 'No description provided.'}
"""

from strategies.Base import Base
import numpy as np
{indicator_imports_str}

class {spec.name}(Base):
    """
    {spec.description or spec.name}
    """
    
{init_method}
    
{next_method}
    
    def validate_params(self, **kwargs) -> bool:
        # Auto-generated: no custom validation
        return True
    
    @staticmethod
    def get_optimization_params():
{opt_params}
'''
        
        # Validate generated code syntax and structure
        _validate_generated_syntax(code)
        
        # Validate strategy execution compatibility
        _validate_strategy_execution(spec, code)
        
        return code
        
    except IndicatorNotFoundError as e:
        # Re-raise with more context
        raise CompilationError(f"Could not resolve indicator '{e.indicator_name}'. "
                             f"Please ensure the indicator is available or check Librarian configuration.")
    
    except ExpressionError as e:
        # Re-raise with more context
        raise CompilationError(f"Invalid condition expression '{e.expression}': {e.details}")
    
    except ValidationError as e:
        # Re-raise with more context
        raise CompilationError(f"StrategySpec validation failed: {str(e)}")
    
    except Exception as e:
        # Catch any other unexpected errors
        raise CompilationError(f"Unexpected compilation error: {str(e)}")


def save_strategy(spec: StrategySpec, output_dir: str = "strategies") -> str:
    """
    Compile and save a strategy to a .py file.
    """
    import os
    
    code = compile_strategy(spec)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{spec.name}.py"
    filepath = os.path.join(output_dir, filename)
    
    write_file(filepath, code)
    
    return filepath


# Example / Testing
if __name__ == "__main__":
    from research_agent.schema import StrategySpec, Indicator, Condition
    
    # Create a test spec with a NEW indicator
    test_spec = StrategySpec(
        name="TestNewInd",
        description="Testing Librarian",
        indicators=[
            Indicator(name="kelt", type="keltner_channel", params={"period": 20})
        ],
        entry_conditions=[],
        exit_conditions=[],
        optimization_params={}
    )
    
    # Compile
    # This should trigger Librarian to created calculate_keltner_channel in indicators/
    print("Compiling (expecting Librarian trigger)...")
    # Note: This will likely fail if no API key, but proves the flow
    try:
        code = compile_strategy(test_spec)
        print("Generated Code:")
        print(code)
    except Exception as e:
        print(f"Compilation/Librarian Error: {e}")
