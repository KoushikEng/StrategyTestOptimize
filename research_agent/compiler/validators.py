"""
Validation functions for StrategySpec and generated code.
"""

import ast
import re
from typing import List
from research_agent.schema import StrategySpec, Condition
from research_agent.tools import write_file
from .exceptions import ValidationError, ExpressionError, CompilationError


def validate_strategy_spec(spec: StrategySpec) -> None:
    """Validate StrategySpec before compilation."""
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
        
        reserved_keywords = {'and', 'or', 'not', 'if', 'else', 'elif', 'for', 'while', 'def', 'class', 'import', 'from'}
        if indicator.name in reserved_keywords:
            raise ValidationError(f"Indicator name '{indicator.name}' is a reserved Python keyword")
    
    # Validate condition expressions
    for condition in spec.entry_conditions + spec.exit_conditions:
        validate_condition_expression(condition.expression)


def validate_condition_expression(expression: str) -> None:
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


def validate_generated_code(code: str) -> None:
    """Validate that generated code has correct syntax and structure."""
    try:
        tree = ast.parse(code)
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
    
    # Validate enhanced patterns are used
    if 'def run(self, data, **kwargs):' in code:
        raise CompilationError("Generated code must not contain old-style run() method")
    
    if 'for i in range(' in code:
        raise CompilationError("Generated code must not contain manual loops")
    
    if 'in_position = False' in code or 'in_position = True' in code:
        raise CompilationError("Generated code must not use manual position tracking")