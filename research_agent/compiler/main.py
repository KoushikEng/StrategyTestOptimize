"""
Main compiler entry point.
"""

import os
from typing import Dict
from research_agent.schema import StrategySpec
from research_agent.tools import write_file

from .validators import validate_strategy_spec, validate_generated_code
from .indicator_registry import IndicatorManager
from .expression_transformer import ExpressionTransformer
from .position_logic import PositionLogicGenerator
from .exceptions import CompilationError, IndicatorNotFoundError, ExpressionError, ValidationError


def compile_strategy(spec: StrategySpec) -> str:
    """
    Compile a StrategySpec into executable Python code using enhanced Base framework.
    """
    try:
        # Validate input
        validate_strategy_spec(spec)
        
        # Initialize components
        indicator_manager = IndicatorManager()
        transformer = ExpressionTransformer()
        position_generator = PositionLogicGenerator()
        
        # Generate imports
        indicator_imports = indicator_manager.generate_imports(spec.indicators)
        
        # Generate init method
        init_method = _generate_init_method(spec.indicators, indicator_manager)
        
        # Extract indicator names for transformation
        all_conditions = spec.entry_conditions + spec.exit_conditions
        indicator_names = transformer.extract_indicator_names(all_conditions)
        
        # Add indicator names from spec
        for indicator in spec.indicators:
            indicator_names.add(indicator.name)
        
        # Generate next method with proper position logic
        position_type = getattr(spec, 'position_type', 'long')
        next_method = position_generator.generate_next_method(
            spec.entry_conditions, 
            spec.exit_conditions, 
            indicator_names, 
            position_type
        )
        
        # Generate optimization parameters
        opt_params = _generate_optimization_params(spec.optimization_params)
        
        # Build the complete strategy code
        code = _build_strategy_code(
            spec.name,
            spec.description,
            indicator_imports,
            init_method,
            next_method,
            opt_params
        )
        
        # Validate generated code
        validate_generated_code(code)
        
        return code
        
    except (IndicatorNotFoundError, ExpressionError, ValidationError) as e:
        raise CompilationError(str(e))
    except Exception as e:
        raise CompilationError(f"Unexpected compilation error: {str(e)}")


def save_strategy(spec: StrategySpec, output_dir: str = "strategies") -> str:
    """
    Compile and save a strategy to a .py file.
    """
    code = compile_strategy(spec)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{spec.name}.py"
    filepath = os.path.join(output_dir, filename)
    
    write_file(filepath, code)
    
    return filepath


def _generate_init_method(indicators, indicator_manager: IndicatorManager) -> str:
    """Generate init() method with indicator registrations."""
    if not indicators:
        return '''    def init(self):
        """Initialize strategy indicators and parameters."""
        pass'''
    
    registrations = indicator_manager.generate_registrations(indicators)
    
    return f'''    def init(self):
        """Initialize strategy indicators and parameters."""
{registrations}'''


def _generate_optimization_params(params: Dict[str, tuple]) -> str:
    """Generate get_optimization_params method."""
    if not params:
        return "        return {}"
    
    lines = ["        return {"]
    for key, value in params.items():
        lines.append(f'            "{key}": {value},')
    lines.append("        }")
    
    return "\n".join(lines)


def _build_strategy_code(name: str, description: str, indicator_imports: str, 
                        init_method: str, next_method: str, opt_params: str) -> str:
    """Build the complete strategy code."""
    
    imports_section = ""
    if indicator_imports:
        imports_section = f"\n{indicator_imports}"
    
    return f'''"""
Auto-generated strategy: {name}
{description or 'No description provided.'}
"""

from strategies.Base import Base
import numpy as np{imports_section}


class {name}(Base):
    """
    {description or name}
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