"""
Compiler exception classes.
"""

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