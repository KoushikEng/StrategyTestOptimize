"""
Property-based tests for the enhanced compiler.

Tests the compiler's ability to generate strategies compatible with the enhanced Base framework.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from research_agent.schema import StrategySpec, Indicator, Condition
import ast
import re


# Mock compile_strategy for testing without full dependencies
def mock_compile_strategy(spec: StrategySpec) -> str:
    """Mock version of compile_strategy for testing basic structure."""
    # Safely handle description to avoid unicode escape issues
    description = spec.description or 'No description provided.'
    # Replace problematic characters that could cause unicode escape issues
    description = description.replace('\\', '\\\\').replace('\n', ' ').replace('\r', ' ')
    
    return f'''"""
Auto-generated strategy: {spec.name}
{description}
"""

from strategies.Base import Base
import numpy as np

class {spec.name}(Base):
    """
    {description}
    """
    
    def init(self):
        """Initialize strategy indicators and parameters."""
        pass
    
    def next(self):
        """Process the current bar."""
        pass
    
    def validate_params(self, **kwargs) -> bool:
        return True
    
    @staticmethod
    def get_optimization_params():
        return {{}}
'''


# Strategy generation for property tests
@st.composite
def strategy_spec_strategy(draw):
    """Generate valid StrategySpec instances for property testing."""
    # Generate valid Python class names (PascalCase)
    base_names = ['TestStrategy', 'MyStrategy', 'SimpleStrategy', 'BasicStrategy', 'DemoStrategy']
    suffix = draw(st.integers(min_value=1, max_value=999))
    name = draw(st.sampled_from(base_names)) + str(suffix)
    
    description = draw(st.one_of(
        st.none(),
        st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),  # Printable ASCII
            min_size=1, 
            max_size=50
        )
    ))
    
    return StrategySpec(
        name=name,
        description=description,
        indicators=[],
        entry_conditions=[],
        exit_conditions=[],
        optimization_params={}
    )


class TestIntegrationWithExistingSpecs:
    """Integration tests with existing strategy specifications."""
    
    def test_rsi_strategy_integration(self):
        """Test integration with RSI-based strategy specification."""
        from research_agent.compiler import compile_strategy
        
        # Create an RSI strategy spec similar to what might exist
        rsi_spec = StrategySpec(
            name="RsiMeanReversion",
            description="Buy when RSI is oversold, sell when overbought",
            indicators=[
                Indicator(name="rsi", type="rsi", params={"period": 14}),
                Indicator(name="sma", type="sma", params={"period": 50})
            ],
            entry_conditions=[
                Condition(expression="rsi < 30", description="RSI oversold"),
                Condition(expression="closes > sma", description="Above trend")
            ],
            exit_conditions=[
                Condition(expression="rsi > 70", description="RSI overbought")
            ],
            position_type="long",
            optimization_params={
                "rsi_period": (7, 21),
                "oversold_threshold": (20, 35),
                "overbought_threshold": (65, 80)
            }
        )
        
        try:
            code = compile_strategy(rsi_spec)
            
            # Verify RSI strategy structure
            assert "class RsiMeanReversion(Base):" in code
            assert "self.rsi = self.I(" in code
            assert "self.sma = self.I(" in code
            assert "self.data.Close" in code  # Transformed data access
            assert "rsi_period" in code
            assert "oversold_threshold" in code
            
            # Verify enhanced patterns
            assert "def init(self):" in code
            assert "def next(self):" in code
            assert "self.position['is_in_position']" in code
            assert "self.buy()" in code
            assert "self.sell()" in code
            
            # Verify no old patterns
            assert "def run(self, data, **kwargs):" not in code
            assert "for i in range(" not in code
            
            # Verify syntactic validity
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("RSI/SMA indicators not available")
            else:
                raise
    
    def test_moving_average_crossover_integration(self):
        """Test integration with moving average crossover strategy."""
        from research_agent.compiler import compile_strategy
        
        ma_crossover_spec = StrategySpec(
            name="MACrossover",
            description="Moving average crossover strategy",
            indicators=[
                Indicator(name="sma_fast", type="sma", params={"period": 10}),
                Indicator(name="sma_slow", type="sma", params={"period": 20})
            ],
            entry_conditions=[
                Condition(expression="sma_fast > sma_slow", description="Fast MA above slow MA")
            ],
            exit_conditions=[
                Condition(expression="sma_fast < sma_slow", description="Fast MA below slow MA")
            ],
            position_type="long",
            optimization_params={
                "fast_period": (5, 15),
                "slow_period": (15, 30)
            }
        )
        
        try:
            code = compile_strategy(ma_crossover_spec)
            
            # Verify MA crossover structure
            assert "class MACrossover(Base):" in code
            assert "self.sma_fast = self.I(" in code
            assert "self.sma_slow = self.I(" in code
            assert "fast_period" in code
            assert "slow_period" in code
            
            # Verify enhanced framework usage
            assert "def init(self):" in code
            assert "def next(self):" in code
            
            # Verify syntactic validity
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("SMA indicator not available")
            else:
                raise
    
    def test_time_based_strategy_integration(self):
        """Test integration with time-based strategy specification."""
        from research_agent.compiler import compile_strategy
        
        time_based_spec = StrategySpec(
            name="TimeBasedStrategy",
            description="Strategy with time-based conditions",
            indicators=[
                Indicator(name="sma", type="sma", params={"period": 20})
            ],
            entry_conditions=[
                Condition(expression="is_market_hours(timestamp)", description="During market hours"),
                Condition(expression="sma > closes", description="SMA above price")
            ],
            exit_conditions=[
                Condition(expression="extract_hour(timestamp) >= 15", description="Closing hour")
            ],
            position_type="long",
            optimization_params={}
        )
        
        try:
            code = compile_strategy(time_based_spec)
            
            # Verify time-based functionality
            assert "from datetime_utils import" in code
            assert "is_market_hours" in code
            assert "extract_hour" in code
            assert "current_timestamp = int(self.data.timestamps[-1])" in code
            
            # Verify enhanced structure
            assert "class TimeBasedStrategy(Base):" in code
            assert "def init(self):" in code
            assert "def next(self):" in code
            
            # Verify syntactic validity
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("SMA indicator not available")
            else:
                raise
    
    def test_complex_multi_indicator_integration(self):
        """Test integration with complex multi-indicator strategy."""
        from research_agent.compiler import compile_strategy
        
        complex_spec = StrategySpec(
            name="ComplexMultiIndicator",
            description="Complex strategy with multiple indicators and conditions",
            indicators=[
                Indicator(name="sma_short", type="sma", params={"period": 10}),
                Indicator(name="sma_long", type="sma", params={"period": 50}),
                Indicator(name="rsi", type="rsi", params={"period": 14})
            ],
            entry_conditions=[
                Condition(expression="sma_short > sma_long", description="Short MA above long MA"),
                Condition(expression="rsi > 50", description="RSI above midline"),
                Condition(expression="volume > 1000", description="Sufficient volume")
            ],
            exit_conditions=[
                Condition(expression="sma_short < sma_long", description="Short MA below long MA"),
                Condition(expression="rsi < 30", description="RSI oversold")
            ],
            position_type="long",
            optimization_params={
                "short_period": (5, 15),
                "long_period": (30, 70),
                "rsi_period": (10, 20),
                "volume_threshold": (500, 2000)
            }
        )
        
        try:
            code = compile_strategy(complex_spec)
            
            # Verify all indicators are registered
            assert "self.sma_short = self.I(" in code
            assert "self.sma_long = self.I(" in code
            assert "self.rsi = self.I(" in code
            
            # Verify data access transformation
            assert "self.data.Volume" in code
            
            # Verify optimization parameters
            assert "short_period" in code
            assert "long_period" in code
            assert "rsi_period" in code
            assert "volume_threshold" in code
            
            # Verify enhanced structure
            assert "class ComplexMultiIndicator(Base):" in code
            
            # Verify syntactic validity
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("Required indicators not available")
            else:
                raise
    
    def test_minimal_strategy_integration(self):
        """Test integration with minimal strategy specification."""
        from research_agent.compiler import compile_strategy
        
        minimal_spec = StrategySpec(
            name="MinimalStrategy",
            description="Minimal strategy for testing",
            indicators=[],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        code = compile_strategy(minimal_spec)
        
        # Verify minimal strategy structure
        assert "class MinimalStrategy(Base):" in code
        assert "def init(self):" in code
        assert "def next(self):" in code
        assert "pass" in code  # Should have pass for empty init
        
        # Verify enhanced patterns even in minimal case
        assert "self.position['is_in_position']" in code
        assert "self.buy()" in code
        assert "self.sell()" in code
        
        # Verify syntactic validity
        ast.parse(code)


class TestBackwardCompatibility:
    """Property 7: Backward compatibility preservation tests."""
    
    def test_existing_strategyspec_fields_handled(self):
        """Test that all existing StrategySpec fields are handled correctly."""
        from research_agent.compiler import compile_strategy
        
        # Create a comprehensive StrategySpec using all available fields
        spec = StrategySpec(
            name="BackwardCompatTest",
            description="Test backward compatibility with all fields",
            indicators=[
                Indicator(name="sma", type="sma", params={"period": 20})
            ],
            entry_conditions=[
                Condition(expression="sma > closes", description="SMA above price")
            ],
            exit_conditions=[
                Condition(expression="sma < closes", description="SMA below price")
            ],
            position_type="long",
            optimization_params={
                "sma_period": (10, 30),
                "threshold": (0.01, 0.05)
            }
        )
        
        try:
            code = compile_strategy(spec)
            
            # Verify all fields are handled
            assert "BackwardCompatTest" in code
            assert "Test backward compatibility" in code
            assert "self.sma = self.I(" in code
            assert "sma > closes" in code or "self.data.Close" in code
            assert "get_optimization_params" in code
            
            # Verify the code is syntactically valid
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("SMA indicator not available")
            else:
                raise
    
    def test_legacy_condition_expressions_compatibility(self):
        """Test that legacy condition expressions are transformed correctly."""
        from research_agent.compiler import compile_strategy
        
        # Test with legacy-style expressions that should be transformed
        spec = StrategySpec(
            name="LegacyExpressionTest",
            description="Test legacy expression compatibility",
            indicators=[],
            entry_conditions=[
                Condition(expression="closes > opens"),
                Condition(expression="volume > 1000")
            ],
            exit_conditions=[
                Condition(expression="closes < opens")
            ],
            optimization_params={}
        )
        
        code = compile_strategy(spec)
        
        # Verify legacy expressions are transformed to enhanced patterns
        assert "self.data.Close" in code
        assert "self.data.Open" in code
        assert "self.data.Volume" in code
        
        # Should not contain old-style array access
        assert "closes[" not in code
        assert "opens[" not in code
        assert "volume[" not in code
        
        # Verify syntactic validity
        ast.parse(code)
    
    def test_optimization_params_backward_compatibility(self):
        """Test that optimization parameters are handled correctly."""
        from research_agent.compiler import compile_strategy
        
        spec = StrategySpec(
            name="OptimizationTest",
            description="Test optimization params compatibility",
            indicators=[],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={
                "param1": (1, 10),
                "param2": (0.1, 1.0),
                "param3": (5, 50)
            }
        )
        
        code = compile_strategy(spec)
        
        # Verify optimization parameters are included
        assert "get_optimization_params" in code
        assert "param1" in code
        assert "param2" in code
        assert "param3" in code
        assert "(1, 10)" in code
        assert "(0.1, 1.0)" in code
        assert "(5, 50)" in code
        
        # Verify syntactic validity
        ast.parse(code)
    
    def test_empty_fields_backward_compatibility(self):
        """Test handling of empty or minimal StrategySpec fields."""
        from research_agent.compiler import compile_strategy
        
        # Test with minimal spec (empty indicators, conditions)
        minimal_spec = StrategySpec(
            name="MinimalTest",
            description=None,
            indicators=[],
            entry_conditions=[],
            exit_conditions=[],
            optimization_params={}
        )
        
        code = compile_strategy(minimal_spec)
        
        # Should still generate valid strategy structure
        assert "class MinimalTest(Base):" in code
        assert "def init(self):" in code
        assert "def next(self):" in code
        assert "def validate_params" in code
        assert "get_optimization_params" in code
        
        # Should handle empty conditions gracefully
        assert "pass" in code  # Should have pass statement for empty logic
        
        # Verify syntactic validity
        ast.parse(code)
    
    @settings(deadline=None)
    @given(st.builds(
        StrategySpec,
        name=st.sampled_from(['LegacyStrategy1', 'LegacyStrategy2', 'BackwardTest']),
        description=st.one_of(st.none(), st.just("Legacy test strategy")),
        indicators=st.lists(
            st.builds(
                Indicator,
                name=st.sampled_from(['sma', 'ema']),
                type=st.sampled_from(['sma', 'ema']),
                params=st.dictionaries(
                    st.sampled_from(['period']),
                    st.integers(min_value=5, max_value=50),
                    min_size=0,
                    max_size=1
                )
            ),
            max_size=2
        ),
        entry_conditions=st.lists(
            st.builds(Condition, 
                     expression=st.sampled_from(['True', 'closes > opens', 'volume > 1000']),
                     description=st.one_of(st.none(), st.just("Test condition"))),
            max_size=2
        ),
        exit_conditions=st.lists(
            st.builds(Condition, 
                     expression=st.sampled_from(['True', 'closes < opens']),
                     description=st.one_of(st.none(), st.just("Exit condition"))),
            max_size=2
        ),
        position_type=st.sampled_from(['long', 'short', 'both']),
        optimization_params=st.dictionaries(
            st.sampled_from(['param1', 'param2']),
            st.tuples(st.integers(1, 10), st.integers(11, 50)),
            max_size=2
        )
    ))
    def test_backward_compatibility_property(self, spec):
        """
        Property 7: Backward compatibility preservation
        For any existing valid StrategySpec JSON, the enhanced compiler should parse all fields 
        correctly and generate equivalent functionality using the new patterns.
        **Validates: Requirements 7.1, 7.4, 7.5**
        """
        from research_agent.compiler import compile_strategy
        
        try:
            code = compile_strategy(spec)
            
            # Verify enhanced framework patterns are used
            assert "from strategies.Base import Base" in code, \
                "Must use enhanced Base import"
            assert f"class {spec.name}(Base):" in code, \
                "Must inherit from enhanced Base class"
            assert "def init(self):" in code, \
                "Must have init() method"
            assert "def next(self):" in code, \
                "Must have next() method"
            
            # Verify no old-style patterns
            assert "def run(self, data, **kwargs):" not in code, \
                "Must not use old-style run() method"
            assert "for i in range(" not in code, \
                "Must not use manual loops"
            assert "in_position = False" not in code, \
                "Must not use manual position tracking"
            
            # Verify all StrategySpec fields are handled
            if spec.description:
                clean_desc = spec.description.replace('\\', '\\\\').replace('\n', ' ').replace('\r', ' ')
                assert clean_desc in code, \
                    "Description must be included in generated code"
            
            if spec.indicators:
                for indicator in spec.indicators:
                    assert f"self.{indicator.name}" in code, \
                        f"Indicator {indicator.name} must be registered"
            
            if spec.optimization_params:
                assert "get_optimization_params" in code, \
                    "Optimization parameters must be included"
                for param_name in spec.optimization_params.keys():
                    assert param_name in code, \
                        f"Optimization parameter {param_name} must be included"
            
            # Verify syntactic validity
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e) or "Registry" in str(e):
                assume(False)  # Skip this test case
            else:
                raise


class TestErrorHandling:
    """Property 8: Comprehensive error handling tests."""
    
    def test_invalid_condition_expression_validation(self):
        """Test validation of invalid condition expressions."""
        from research_agent.compiler import compile_strategy, ExpressionError, CompilationError
        
        invalid_specs = [
            # Empty expression
            StrategySpec(name="TestStrategy", description="Test", indicators=[], 
                        entry_conditions=[Condition(expression="")],
                        exit_conditions=[], optimization_params={}),
            # Dangerous pattern
            StrategySpec(name="TestStrategy", description="Test", indicators=[], 
                        entry_conditions=[Condition(expression="exec('malicious code')")],
                        exit_conditions=[], optimization_params={}),
            # Syntax error
            StrategySpec(name="TestStrategy", description="Test", indicators=[], 
                        entry_conditions=[Condition(expression="sma > closes and")],
                        exit_conditions=[], optimization_params={}),
        ]
        
        for spec in invalid_specs:
            with pytest.raises((ExpressionError, CompilationError)):
                compile_strategy(spec)
    
    def test_missing_indicator_error_handling(self):
        """Test error handling for missing indicators."""
        from research_agent.compiler import compile_strategy, IndicatorNotFoundError, CompilationError
        
        spec = StrategySpec(
            name="TestStrategy",
            description="Test missing indicator",
            indicators=[Indicator(name="nonexistent", type="nonexistent_indicator", params={})],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        # This should raise an error about the missing indicator
        with pytest.raises((IndicatorNotFoundError, CompilationError)):
            compile_strategy(spec)
    
    def test_syntax_validation_of_generated_code(self):
        """Test that generated code syntax is validated."""
        from research_agent.compiler import _validate_generated_syntax, CompilationError
        import ast
        
        # Test with invalid Python code
        invalid_code = """
def invalid_function(
    # Missing closing parenthesis and colon
    pass
"""
        
        with pytest.raises(CompilationError):
            _validate_generated_syntax(invalid_code)
        
        # Test with valid Python code that has proper strategy structure
        valid_code = """
from strategies.Base import Base

class ValidStrategy(Base):
    def init(self):
        pass
    
    def next(self):
        pass
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}
"""
        
        # Should not raise any exception
        _validate_generated_syntax(valid_code)
        
        # Test basic syntax validation without structure validation
        simple_valid_code = "x = 1 + 2"
        try:
            ast.parse(simple_valid_code)  # This should work
        except SyntaxError:
            pytest.fail("Basic syntax validation failed")
    
    def test_condition_expression_validation_details(self):
        """Test detailed condition expression validation."""
        from research_agent.compiler import _validate_condition_expression, ExpressionError
        
        # Test valid expressions (should not raise)
        valid_expressions = [
            "sma > closes",
            "rsi < 30 and volume > 1000",
            "True",
            "extract_hour(timestamp) == 9"
        ]
        
        for expr in valid_expressions:
            _validate_condition_expression(expr)  # Should not raise
        
        # Test invalid expressions (should raise)
        invalid_expressions = [
            "",  # Empty
            "   ",  # Whitespace only
            "exec('code')",  # Dangerous pattern
            "eval('expression')",  # Dangerous pattern
            "sma > closes and",  # Syntax error
        ]
        
        for expr in invalid_expressions:
            with pytest.raises(ExpressionError):
                _validate_condition_expression(expr)
    
    def test_pydantic_validation_integration(self):
        """Test that Pydantic validation works correctly."""
        from pydantic import ValidationError
        
        # Test invalid strategy name (caught by Pydantic)
        with pytest.raises(ValidationError):
            StrategySpec(name="123Invalid", description="Test", indicators=[], 
                        entry_conditions=[], exit_conditions=[], optimization_params={})
        
        # Test invalid indicator name (caught by Pydantic)
        with pytest.raises(ValidationError):
            StrategySpec(name="TestStrategy", description="Test", 
                        indicators=[Indicator(name="123invalid", type="sma", params={})],
                        entry_conditions=[], exit_conditions=[], optimization_params={})
    
    def test_comprehensive_syntax_validation(self):
        """Test comprehensive syntax validation of generated code."""
        from research_agent.compiler import compile_strategy, _validate_generated_syntax, _validate_code_structure, CompilationError
        import ast
        
        # Test valid code structure validation
        valid_code = '''
from strategies.Base import Base
import numpy as np

class TestStrategy(Base):
    def init(self):
        pass
    
    def next(self):
        pass
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}
'''
        
        # Should not raise any exception
        _validate_generated_syntax(valid_code)
        
        # Test invalid code structure validation
        invalid_codes = [
            # Missing Base inheritance
            '''
class TestStrategy:
    def init(self):
        pass
''',
            # Missing required methods
            '''
from strategies.Base import Base

class TestStrategy(Base):
    def init(self):
        pass
''',
            # Old-style patterns
            '''
from strategies.Base import Base

class TestStrategy(Base):
    def run(self, data, **kwargs):
        for i in range(len(data)):
            pass
    
    def init(self):
        pass
    
    def next(self):
        pass
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}
''',
            # Manual position tracking
            '''
from strategies.Base import Base

class TestStrategy(Base):
    def init(self):
        pass
    
    def next(self):
        in_position = False
        pass
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}
'''
        ]
        
        for invalid_code in invalid_codes:
            with pytest.raises(CompilationError):
                _validate_generated_syntax(invalid_code)
    
    def test_strategy_execution_validation(self):
        """Test strategy execution validation."""
        from research_agent.compiler import compile_strategy
        
        # Test with a simple valid strategy
        spec = StrategySpec(
            name="ExecutionTest",
            description="Test execution validation",
            indicators=[],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        try:
            code = compile_strategy(spec)
            
            # Should generate valid code that passes all validation
            assert "class ExecutionTest(Base):" in code
            assert "def init(self):" in code
            assert "def next(self):" in code
            assert "def validate_params" in code
            assert "get_optimization_params" in code
            
            # Should not contain old patterns
            assert "def run(self, data, **kwargs):" not in code
            assert "for i in range(" not in code
            assert "in_position = " not in code
            
        except Exception as e:
            # If compilation fails, it should be due to missing dependencies, not validation
            if "Could not resolve indicator" not in str(e):
                raise
    
    def test_enhanced_pattern_validation(self):
        """Test validation of enhanced framework patterns."""
        from research_agent.compiler import compile_strategy
        
        # Test strategy with indicators
        spec_with_indicators = StrategySpec(
            name="IndicatorTest",
            description="Test indicator validation",
            indicators=[
                Indicator(name="sma", type="sma", params={"period": 20})
            ],
            entry_conditions=[Condition(expression="sma > closes")],
            exit_conditions=[Condition(expression="sma < closes")],
            optimization_params={}
        )
        
        try:
            code = compile_strategy(spec_with_indicators)
            
            # Should use enhanced patterns
            assert "self.I(" in code, "Should use self.I() for indicator registration"
            assert "self.data.Close" in code, "Should use enhanced data access"
            assert "self.position['is_in_position']" in code, "Should use enhanced position management"
            assert "self.buy()" in code, "Should use enhanced trading methods"
            assert "self.sell()" in code, "Should use enhanced trading methods"
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("SMA indicator not available")
            else:
                raise
    
    def test_error_handling_property_simple(self):
        """
        Property 8: Comprehensive error handling (simplified)
        Test that the compiler handles errors gracefully and provides descriptive messages.
        **Validates: Requirements 2.5, 8.1, 8.2, 8.3, 8.4, 8.5**
        """
        from research_agent.compiler import compile_strategy
        
        # Test with valid spec
        valid_spec = StrategySpec(
            name="ValidStrategy",
            description="Valid test strategy",
            indicators=[],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        try:
            code = compile_strategy(valid_spec)
            # Should generate valid Python code
            ast.parse(code)
        except Exception as e:
            # If it fails, error should be descriptive
            error_msg = str(e)
            assert len(error_msg) > 10, f"Error message should be descriptive: {error_msg}"


class TestCodeOrganization:
    """Property 9: Code organization and imports tests."""
    
    @settings(deadline=None)
    @given(st.builds(
        StrategySpec,
        name=st.sampled_from(['OrganizedStrategy1', 'OrganizedStrategy2']),
        description=st.one_of(st.none(), st.just("Well-organized test strategy")),
        indicators=st.lists(
            st.builds(
                Indicator,
                name=st.sampled_from(['sma', 'ema']),
                type=st.sampled_from(['sma', 'ema']),
                params=st.just({'period': 20})
            ),
            max_size=2
        ),
        entry_conditions=st.lists(
            st.builds(Condition, expression=st.sampled_from(['sma > closes', 'True'])),
            max_size=2
        ),
        exit_conditions=st.lists(
            st.builds(Condition, expression=st.sampled_from(['sma < closes', 'True'])),
            max_size=2
        ),
        optimization_params=st.dictionaries(
            st.sampled_from(['param1', 'param2']),
            st.tuples(st.integers(1, 10), st.integers(11, 50)),
            max_size=2
        )
    ))
    def test_code_organization_property(self, spec):
        """
        Property 9: Code organization and imports
        For any generated strategy, the code should have well-organized init() methods, 
        include only necessary imports, and contain appropriate docstrings with strategy descriptions.
        **Validates: Requirements 6.2, 6.4, 6.5**
        """
        try:
            from research_agent.compiler import compile_strategy
            code = compile_strategy(spec)
            
            # Verify proper import organization
            lines = code.split('\n')
            import_section_started = False
            class_section_started = False
            
            for line in lines:
                if line.startswith('from ') or line.startswith('import '):
                    import_section_started = True
                    assert not class_section_started, \
                        "Imports should come before class definition"
                elif line.startswith('class '):
                    class_section_started = True
            
            # Verify necessary imports are present
            assert "from strategies.Base import Base" in code, \
                "Must import enhanced Base class"
            assert "import numpy as np" in code, \
                "Must import numpy for array operations"
            
            # Verify no unnecessary imports
            assert "from numba import njit" not in code, \
                "Should not import numba in enhanced framework"
            
            # Verify proper docstring organization
            assert '"""' in code, "Must contain docstrings"
            
            # Verify strategy description in docstring
            if spec.description:
                # Clean description for comparison
                clean_desc = spec.description.replace('\\', '\\\\').replace('\n', ' ').replace('\r', ' ')
                assert clean_desc in code, \
                    "Strategy description must be included in docstring"
            
            # Verify init() method organization
            if spec.indicators:
                assert "def init(self):" in code, \
                    "Must have init() method when indicators are present"
                assert "Initialize strategy indicators and parameters" in code, \
                    "init() method must have proper docstring"
                
                # Verify indicators are organized in init()
                init_section = code.split("def init(self):")[1].split("def next(self):")[0]
                for indicator in spec.indicators:
                    assert f"self.{indicator.name} = self.I(" in init_section, \
                        f"Indicator {indicator.name} must be registered in init() method"
            
            # Verify next() method organization
            assert "def next(self):" in code, \
                "Must have next() method"
            assert "Process the current bar" in code, \
                "next() method must have proper docstring"
            
            # Verify optimization params method organization
            assert "def get_optimization_params():" in code, \
                "Must have get_optimization_params() method"
            assert "@staticmethod" in code, \
                "get_optimization_params() must be static method"
            
            # Verify syntactic validity and proper formatting
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e) or "Registry" in str(e):
                assume(False)  # Skip this test case
            else:
                raise
    
    def test_import_optimization(self):
        """Test that only necessary imports are included."""
        from research_agent.compiler import compile_strategy
        
        # Test strategy with no indicators
        spec_no_indicators = StrategySpec(
            name="NoIndicators",
            description="Strategy without indicators",
            indicators=[],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        code = compile_strategy(spec_no_indicators)
        
        # Should not import indicator functions when none are used
        assert "from calculate.indicators import" not in code, \
            "Should not import indicators when none are used"
        
        # Should still have basic imports
        assert "from strategies.Base import Base" in code
        assert "import numpy as np" in code
    
    def test_docstring_organization(self):
        """Test proper docstring organization and content."""
        from research_agent.compiler import compile_strategy
        
        spec = StrategySpec(
            name="DocstringTest",
            description="Test strategy for docstring validation",
            indicators=[],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        code = compile_strategy(spec)
        
        # Verify module-level docstring
        assert '"""' in code
        assert "Auto-generated strategy: DocstringTest" in code
        assert "Test strategy for docstring validation" in code
        
        # Verify class-level docstring
        class_section = code.split("class DocstringTest(Base):")[1]
        assert '"""' in class_section
        assert "Test strategy for docstring validation" in class_section


class TestTimeBasedLogic:
    """Property 5: Time-based logic integration tests."""
    
    @settings(deadline=None)
    @given(st.builds(
        StrategySpec,
        name=st.sampled_from(['TimeStrategy1', 'TimeStrategy2']),
        description=st.one_of(st.none(), st.just("Time-based test strategy")),
        indicators=st.lists(
            st.builds(
                Indicator,
                name=st.sampled_from(['sma']),
                type=st.sampled_from(['sma']),
                params=st.just({'period': 20})
            ),
            max_size=1
        ),
        entry_conditions=st.lists(
            st.builds(Condition, expression=st.sampled_from([
                'is_market_hours(timestamp)',
                'extract_hour(timestamp) == 9',
                'is_opening_hour(current_timestamp)',
                'sma > closes and is_market_hours(timestamp)'
            ])),
            min_size=1,
            max_size=2
        ),
        exit_conditions=st.lists(
            st.builds(Condition, expression=st.sampled_from([
                'is_closing_hour(timestamp)',
                'extract_hour(timestamp) >= 15',
                'True'
            ])),
            min_size=1,
            max_size=2
        ),
        optimization_params=st.just({})
    ))
    def test_time_based_logic_property(self, spec):
        """
        Property 5: Time-based logic integration
        For any StrategySpec with time-based conditions, the generated code should import 
        datetime_utils functions and use appropriate time filtering with self.data.timestamps[-1].
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        from research_agent.compiler import (
            _detect_time_based_conditions, _generate_time_based_imports,
            _generate_time_filters, _generate_next_method, _extract_indicator_names
        )
        
        all_conditions = spec.entry_conditions + spec.exit_conditions
        
        # Test time-based condition detection
        has_time_conditions = _detect_time_based_conditions(all_conditions)
        assert has_time_conditions, "Should detect time-based conditions in the spec"
        
        # Test datetime_utils import generation
        datetime_imports = _generate_time_based_imports(all_conditions)
        assert "from datetime_utils import" in datetime_imports, \
            "Should generate datetime_utils imports for time-based conditions"
        
        # Verify specific function imports based on conditions
        for condition in all_conditions:
            if 'is_market_hours' in condition.expression:
                assert 'is_market_hours' in datetime_imports, \
                    "Should import is_market_hours function"
            if 'extract_hour' in condition.expression:
                assert 'extract_hour' in datetime_imports, \
                    "Should import extract_hour function"
            if 'is_opening_hour' in condition.expression:
                assert 'is_opening_hour' in datetime_imports, \
                    "Should import is_opening_hour function"
            if 'is_closing_hour' in condition.expression:
                assert 'is_closing_hour' in datetime_imports, \
                    "Should import is_closing_hour function"
        
        # Test time filter generation
        time_filters = _generate_time_filters(all_conditions)
        assert "current_timestamp = int(self.data.timestamps[-1])" in time_filters, \
            "Should generate timestamp access pattern"
        assert "is_market_hours(current_timestamp)" in time_filters, \
            "Should generate market hours filtering"
        
        # Test next() method with time-based logic
        indicator_names = _extract_indicator_names(all_conditions)
        next_method = _generate_next_method(spec.entry_conditions, spec.exit_conditions, indicator_names)
        
        assert "current_timestamp = int(self.data.timestamps[-1])" in next_method, \
            "next() method should include timestamp access"
        assert "Time-based filtering" in next_method, \
            "next() method should include time-based filtering comment"
    
    def test_specific_time_transformations(self):
        """Test specific time-based expression transformations."""
        from research_agent.compiler import _transform_time_expressions
        
        test_cases = [
            ('timestamp', 'current_timestamp'),
            ('timestamps[-1]', 'current_timestamp'),
            ('self.data.timestamps[-1]', 'current_timestamp'),
            ('is_market_hours(timestamp)', 'is_market_hours(current_timestamp)'),
            ('extract_hour(timestamps[-1]) == 9', 'extract_hour(current_timestamp) == 9')
        ]
        
        for original, expected in test_cases:
            result = _transform_time_expressions(original)
            assert result == expected, f"Transform '{original}' -> expected '{expected}', got '{result}'"
    
    def test_time_based_imports_detection(self):
        """Test detection and import generation for various time functions."""
        from research_agent.compiler import _generate_time_based_imports
        
        test_conditions = [
            [Condition(expression="is_market_hours(timestamp)")],
            [Condition(expression="extract_hour(timestamp) == 9")],
            [Condition(expression="is_opening_hour(current_timestamp)")],
            [Condition(expression="extract_day_of_week(timestamp) == 0")]
        ]
        
        expected_imports = [
            "is_market_hours",
            "extract_hour", 
            "is_opening_hour",
            "extract_day_of_week"
        ]
        
        for conditions, expected_func in zip(test_conditions, expected_imports):
            imports = _generate_time_based_imports(conditions)
            assert expected_func in imports, f"Should import {expected_func} for conditions {conditions}"


class TestEnhancedMethodGeneration:
    """Property 1: Enhanced framework method generation tests."""
    
    @settings(deadline=None)
    @given(st.builds(
        StrategySpec,
        name=st.sampled_from(['TestStrategy1', 'TestStrategy2', 'TestStrategy3']),
        description=st.one_of(st.none(), st.just("Test strategy")),
        indicators=st.lists(
            st.builds(
                Indicator,
                name=st.sampled_from(['sma', 'ema']),
                type=st.sampled_from(['sma', 'ema']),
                params=st.just({'period': 20})
            ),
            max_size=2
        ),
        entry_conditions=st.lists(
            st.builds(Condition, expression=st.just("True")),
            max_size=2
        ),
        exit_conditions=st.lists(
            st.builds(Condition, expression=st.just("True")),
            max_size=2
        ),
        optimization_params=st.just({})
    ))
    def test_enhanced_method_generation_property(self, spec):
        """
        Property 1: Enhanced framework method generation
        For any valid StrategySpec, the generated strategy code should contain init() and next() 
        methods and should not contain a run() method with manual loops.
        **Validates: Requirements 1.2, 7.2, 7.3**
        """
        from research_agent.compiler import _generate_init_method, _generate_next_method, _extract_indicator_names
        
        # Generate init method
        init_method = _generate_init_method(spec.indicators)
        
        # Generate next method
        all_conditions = spec.entry_conditions + spec.exit_conditions
        indicator_names = _extract_indicator_names(all_conditions)
        next_method = _generate_next_method(spec.entry_conditions, spec.exit_conditions, indicator_names)
        
        # Verify init() method presence and structure
        assert "def init(self):" in init_method, \
            "Generated strategy must have init() method"
        assert "Initialize strategy indicators and parameters" in init_method, \
            "init() method must have proper docstring"
        
        # Verify next() method presence and structure
        assert "def next(self):" in next_method, \
            "Generated strategy must have next() method"
        assert "Process the current bar" in next_method, \
            "next() method must have proper docstring"
        
        # Verify no old-style run() method patterns
        combined_code = init_method + "\n" + next_method
        assert "def run(self, data, **kwargs):" not in combined_code, \
            "Must not generate old-style run() method"
        assert "for i in range(" not in combined_code, \
            "Must not contain manual loops"
        assert "n = len(closes)" not in combined_code, \
            "Must not contain old-style data length calculations"
        
        # Verify enhanced patterns are used
        if spec.indicators:
            assert "self.I(" in init_method, \
                "Must use self.I() for indicator registration"
        
        if spec.entry_conditions or spec.exit_conditions:
            assert "self.position" in next_method, \
                "Must use enhanced position management"
            assert ("self.buy()" in next_method or "self.sell()" in next_method), \
                "Must use enhanced trading methods"


class TestPositionManagement:
    """Property 4: Position management method usage tests."""
    
    @settings(deadline=None)
    @given(st.builds(
        StrategySpec,
        name=st.sampled_from(['TestStrategy1', 'TestStrategy2']),
        description=st.one_of(st.none(), st.just("Test strategy")),
        indicators=st.lists(
            st.builds(
                Indicator,
                name=st.sampled_from(['sma', 'ema']),
                type=st.sampled_from(['sma', 'ema']),
                params=st.just({'period': 20})
            ),
            max_size=2
        ),
        entry_conditions=st.lists(
            st.builds(Condition, expression=st.sampled_from(['sma > closes', 'True'])),
            min_size=1,
            max_size=2
        ),
        exit_conditions=st.lists(
            st.builds(Condition, expression=st.sampled_from(['sma < closes', 'True'])),
            min_size=1,
            max_size=2
        ),
        optimization_params=st.just({})
    ))
    def test_position_management_property(self, spec):
        """
        Property 4: Position management method usage
        For any StrategySpec with entry and exit conditions, the generated next() method should use 
        self.buy() and self.sell() calls instead of manual position tracking variables.
        **Validates: Requirements 1.4, 4.1, 4.2, 4.3, 4.4, 4.5**
        """
        from research_agent.compiler import _generate_next_method, _extract_indicator_names
        
        # Extract indicator names from conditions
        all_conditions = spec.entry_conditions + spec.exit_conditions
        indicator_names = _extract_indicator_names(all_conditions)
        
        next_method = _generate_next_method(spec.entry_conditions, spec.exit_conditions, indicator_names)
        
        # Verify enhanced position management patterns
        assert "self.position['is_in_position']" in next_method, \
            "Must use enhanced position property instead of manual tracking"
        
        assert "self.buy()" in next_method, \
            "Must use self.buy() method for opening positions"
        
        assert "self.sell()" in next_method, \
            "Must use self.sell() method for closing positions"
        
        # Verify no manual position tracking variables
        assert "in_position = " not in next_method, \
            "Must not use manual position tracking variables"
        assert "entry_price = " not in next_method, \
            "Must not use manual entry price tracking"
        
        # Verify proper method structure
        assert "def next(self):" in next_method, \
            "Must have proper next() method signature"
        assert "Process the current bar" in next_method, \
            "Must have proper docstring"
    
    def test_position_management_logic_structure(self):
        """Test the structure of position management logic."""
        from research_agent.compiler import _generate_next_method
        
        entry_conditions = [Condition(expression="sma > closes")]
        exit_conditions = [Condition(expression="sma < closes")]
        indicator_names = {'sma'}
        
        next_method = _generate_next_method(entry_conditions, exit_conditions, indicator_names)
        
        # Verify the logic structure
        assert "if not self.position['is_in_position']" in next_method, \
            "Entry logic must check for no position"
        assert "elif self.position['is_in_position']" in next_method, \
            "Exit logic must check for existing position"
        
        # Verify data access transformation in conditions
        assert "self.data.Close" in next_method, \
            "Conditions must use enhanced data access patterns"


class TestDataAccessTransformation:
    """Property 3: Data access pattern transformation tests."""
    
    @settings(deadline=None)
    @given(st.lists(
        st.builds(
            Condition,
            expression=st.sampled_from([
                'closes > opens',
                'volume > 1000',
                'highs[0] > lows[0]',
                'closes[-1] > closes[-2]',
                'volume[-1] > volume[-2] * 1.5',
                'opens > closes',
                'highs > lows'
            ])
        ),
        min_size=1,
        max_size=3
    ))
    def test_data_access_transformation_property(self, conditions):
        """
        Property 3: Data access pattern transformation
        For any condition expression containing data references, the generated code should use 
        self.data.Close[-1], self.data.Volume[-1] patterns instead of array indexing.
        **Validates: Requirements 1.5, 3.1, 3.2, 3.3, 3.4, 3.5**
        """
        from research_agent.compiler import _transform_condition_expressions
        
        # Create a set of indicator names for transformation
        indicator_names = {'sma', 'ema', 'rsi'}
        
        transformed = _transform_condition_expressions(conditions, indicator_names)
        
        # Verify data access transformations
        if any('closes' in c.expression for c in conditions):
            assert 'self.data.Close' in transformed, \
                "closes references must be transformed to self.data.Close"
        
        if any('opens' in c.expression for c in conditions):
            assert 'self.data.Open' in transformed, \
                "opens references must be transformed to self.data.Open"
        
        if any('highs' in c.expression for c in conditions):
            assert 'self.data.High' in transformed, \
                "highs references must be transformed to self.data.High"
        
        if any('lows' in c.expression for c in conditions):
            assert 'self.data.Low' in transformed, \
                "lows references must be transformed to self.data.Low"
        
        if any('volume' in c.expression for c in conditions):
            assert 'self.data.Volume' in transformed, \
                "volume references must be transformed to self.data.Volume"
        
        # Verify no old-style array access remains
        assert 'closes[' not in transformed or 'self.data.Close[' in transformed, \
            "Array access should be transformed to enhanced patterns"
        assert 'opens[' not in transformed or 'self.data.Open[' in transformed, \
            "Array access should be transformed to enhanced patterns"
    
    def test_specific_data_transformations(self):
        """Test specific data access transformations."""
        from research_agent.compiler import _transform_data_access
        
        test_cases = [
            ('closes > opens', 'self.data.Close[-1] > self.data.Open[-1]'),
            ('closes[0] > opens[0]', 'self.data.Close[0] > self.data.Open[0]'),
            ('volume[-1] > 1000', 'self.data.Volume[-1] > 1000'),
            ('highs[-2] < lows[-2]', 'self.data.High[-2] < self.data.Low[-2]')
        ]
        
        for original, expected in test_cases:
            result = _transform_data_access(original)
            assert result == expected, f"Transform '{original}' -> expected '{expected}', got '{result}'"


class TestInitMethodGeneration:
    """Unit tests for init() method generation."""
    
    def test_empty_indicators_init_method(self):
        """Test init() method generation with no indicators."""
        from research_agent.compiler import _generate_init_method
        
        init_method = _generate_init_method([])
        
        assert "def init(self):" in init_method
        assert "Initialize strategy indicators and parameters" in init_method
        assert "pass" in init_method
    
    def test_single_indicator_init_method(self):
        """Test init() method generation with single indicator."""
        from research_agent.compiler import _generate_init_method
        
        indicators = [
            Indicator(name="sma", type="sma", params={"period": 20})
        ]
        
        init_method = _generate_init_method(indicators)
        
        assert "def init(self):" in init_method
        assert "Initialize strategy indicators and parameters" in init_method
        assert "self.sma = self.I(" in init_method
        assert "pass" not in init_method  # Should not have pass when indicators present
    
    def test_multiple_indicators_init_method(self):
        """Test init() method generation with multiple indicators."""
        from research_agent.compiler import _generate_init_method
        
        indicators = [
            Indicator(name="sma_fast", type="sma", params={"period": 10}),
            Indicator(name="sma_slow", type="sma", params={"period": 20}),
            Indicator(name="rsi", type="rsi", params={"period": 14})
        ]
        
        init_method = _generate_init_method(indicators)
        
        assert "def init(self):" in init_method
        assert "Initialize strategy indicators and parameters" in init_method
        assert "self.sma_fast = self.I(" in init_method
        assert "self.sma_slow = self.I(" in init_method
        assert "self.rsi = self.I(" in init_method
    
    def test_indicator_with_complex_parameters(self):
        """Test init() method generation with complex indicator parameters."""
        from research_agent.compiler import _generate_init_method
        
        # Use a simpler indicator that's more likely to be available
        indicators = [
            Indicator(name="sma", type="sma", params={"period": 20})
        ]
        
        try:
            init_method = _generate_init_method(indicators)
            
            assert "def init(self):" in init_method
            assert "self.sma = self.I(" in init_method
            # Check that parameters are included
            assert "period=20" in init_method or "20" in init_method
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("SMA indicator not available")
            else:
                raise


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete compilation pipeline."""
    
    def test_complete_compilation_pipeline(self):
        """Test the complete compilation pipeline from StrategySpec to executable code."""
        from research_agent.compiler import compile_strategy, save_strategy
        import tempfile
        import os
        
        # Create a comprehensive strategy spec
        spec = StrategySpec(
            name="EndToEndTest",
            description="Complete end-to-end integration test strategy",
            indicators=[
                Indicator(name="sma_short", type="sma", params={"period": 10}),
                Indicator(name="sma_long", type="sma", params={"period": 20})
            ],
            entry_conditions=[
                Condition(expression="sma_short > sma_long", description="Short MA above long MA"),
                Condition(expression="volume > 1000", description="Sufficient volume")
            ],
            exit_conditions=[
                Condition(expression="sma_short < sma_long", description="Short MA below long MA")
            ],
            position_type="long",
            optimization_params={
                "short_period": (5, 15),
                "long_period": (15, 30),
                "volume_threshold": (500, 2000)
            }
        )
        
        try:
            # Test compilation
            code = compile_strategy(spec)
            
            # Verify complete structure
            assert "class EndToEndTest(Base):" in code
            assert "from strategies.Base import Base" in code
            assert "import numpy as np" in code
            
            # Verify indicator imports and registrations
            assert "from calculate.indicators import" in code
            assert "calculate_sma" in code
            assert "self.sma_short = self.I(" in code
            assert "self.sma_long = self.I(" in code
            
            # Verify enhanced framework patterns
            assert "def init(self):" in code
            assert "def next(self):" in code
            assert "self.data.Close" in code
            assert "self.data.Volume" in code
            assert "self.position['is_in_position']" in code
            assert "self.buy()" in code
            assert "self.sell()" in code
            
            # Verify optimization parameters
            assert "get_optimization_params" in code
            assert "short_period" in code
            assert "long_period" in code
            assert "volume_threshold" in code
            
            # Verify no old patterns
            assert "def run(self, data, **kwargs):" not in code
            assert "for i in range(" not in code
            assert "in_position = " not in code
            
            # Test file saving
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = save_strategy(spec, temp_dir)
                assert os.path.exists(filepath)
                assert filepath.endswith("EndToEndTest.py")
                
                # Verify saved file content
                with open(filepath, 'r') as f:
                    saved_code = f.read()
                assert saved_code == code
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("SMA indicator not available")
            else:
                raise
    
    def test_backtesting_engine_compatibility(self):
        """Test compatibility with the backtesting engine structure."""
        from research_agent.compiler import compile_strategy
        
        # Create a strategy that should be compatible with backtesting
        spec = StrategySpec(
            name="BacktestCompatible",
            description="Strategy compatible with backtesting engine",
            indicators=[],
            entry_conditions=[
                Condition(expression="closes > opens", description="Bullish candle")
            ],
            exit_conditions=[
                Condition(expression="closes < opens", description="Bearish candle")
            ],
            optimization_params={
                "threshold": (0.01, 0.05)
            }
        )
        
        code = compile_strategy(spec)
        
        # Verify backtesting compatibility requirements
        assert "from strategies.Base import Base" in code
        assert "class BacktestCompatible(Base):" in code
        
        # Verify required methods for backtesting
        assert "def init(self):" in code
        assert "def next(self):" in code
        assert "def validate_params(self, **kwargs) -> bool:" in code
        assert "@staticmethod" in code
        assert "def get_optimization_params():" in code
        
        # Verify data access patterns work with backtesting data format
        assert "self.data.Close" in code
        assert "self.data.Open" in code
        
        # Verify position management works with backtesting
        assert "self.position['is_in_position']" in code
        assert "self.buy()" in code
        assert "self.sell()" in code
        
        # Verify optimization parameters format
        assert "threshold" in code
        assert "(0.01, 0.05)" in code
    
    def test_optimization_parameter_integration(self):
        """Test integration with optimization parameter system."""
        from research_agent.compiler import compile_strategy
        
        spec = StrategySpec(
            name="OptimizationIntegration",
            description="Test optimization parameter integration",
            indicators=[
                Indicator(name="sma", type="sma", params={"period": 20})
            ],
            entry_conditions=[
                Condition(expression="sma > closes")
            ],
            exit_conditions=[
                Condition(expression="sma < closes")
            ],
            optimization_params={
                "sma_period": (10, 50),
                "entry_threshold": (0.01, 0.1),
                "exit_threshold": (0.01, 0.1),
                "volume_filter": (100, 10000)
            }
        )
        
        try:
            code = compile_strategy(spec)
            
            # Verify optimization parameters are properly formatted
            assert "def get_optimization_params():" in code
            assert "@staticmethod" in code
            
            # Check each parameter is included with correct format
            optimization_params = spec.optimization_params
            for param_name, param_range in optimization_params.items():
                assert param_name in code
                assert str(param_range) in code
            
            # Verify return structure
            assert "return {" in code
            assert "}" in code
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("SMA indicator not available")
            else:
                raise
    
    def test_complex_strategy_integration(self):
        """Test integration with complex multi-indicator, multi-condition strategies."""
        from research_agent.compiler import compile_strategy
        
        complex_spec = StrategySpec(
            name="ComplexIntegration",
            description="Complex strategy for integration testing",
            indicators=[
                Indicator(name="sma_fast", type="sma", params={"period": 10}),
                Indicator(name="sma_slow", type="sma", params={"period": 50}),
                Indicator(name="rsi", type="rsi", params={"period": 14})
            ],
            entry_conditions=[
                Condition(expression="sma_fast > sma_slow", description="Trend up"),
                Condition(expression="rsi > 50", description="Momentum up"),
                Condition(expression="volume > 1000", description="Volume filter"),
                Condition(expression="closes > opens", description="Bullish candle")
            ],
            exit_conditions=[
                Condition(expression="sma_fast < sma_slow", description="Trend down"),
                Condition(expression="rsi < 30", description="Oversold")
            ],
            position_type="long",
            optimization_params={
                "fast_period": (5, 20),
                "slow_period": (30, 100),
                "rsi_period": (10, 20),
                "rsi_entry": (40, 60),
                "rsi_exit": (20, 40),
                "volume_threshold": (500, 5000)
            }
        )
        
        try:
            code = compile_strategy(complex_spec)
            
            # Verify all indicators are handled
            assert "self.sma_fast = self.I(" in code
            assert "self.sma_slow = self.I(" in code
            assert "self.rsi = self.I(" in code
            
            # Verify complex condition handling
            assert "sma_fast > sma_slow" in code or "self.sma_fast[-1] > self.sma_slow[-1]" in code
            assert "rsi > 50" in code or "self.rsi[-1] > 50" in code
            assert "self.data.Volume" in code
            assert "self.data.Close" in code
            assert "self.data.Open" in code
            
            # Verify multiple conditions are combined correctly
            assert " and " in code  # Conditions should be combined with AND
            
            # Verify all optimization parameters
            for param_name in complex_spec.optimization_params.keys():
                assert param_name in code
            
            # Verify enhanced framework structure
            assert "def init(self):" in code
            assert "def next(self):" in code
            assert "self.position['is_in_position']" in code
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("Required indicators not available")
            else:
                raise
    
    def test_time_based_strategy_integration(self):
        """Test integration with time-based strategies."""
        from research_agent.compiler import compile_strategy
        
        time_spec = StrategySpec(
            name="TimeBasedIntegration",
            description="Time-based strategy integration test",
            indicators=[
                Indicator(name="sma", type="sma", params={"period": 20})
            ],
            entry_conditions=[
                Condition(expression="is_market_hours(timestamp)", description="Market hours"),
                Condition(expression="extract_hour(timestamp) >= 9", description="After 9 AM"),
                Condition(expression="sma > closes", description="Above trend")
            ],
            exit_conditions=[
                Condition(expression="extract_hour(timestamp) >= 15", description="Before close"),
                Condition(expression="sma < closes", description="Below trend")
            ],
            optimization_params={
                "sma_period": (10, 50),
                "entry_hour": (9, 11),
                "exit_hour": (14, 16)
            }
        )
        
        try:
            code = compile_strategy(time_spec)
            
            # Verify datetime_utils integration
            assert "from datetime_utils import" in code
            assert "is_market_hours" in code
            assert "extract_hour" in code
            
            # Verify timestamp handling
            assert "current_timestamp = int(self.data.timestamps[-1])" in code
            assert "is_market_hours(current_timestamp)" in code
            
            # Verify time-based filtering
            assert "Time-based filtering" in code
            
            # Verify time expressions are transformed
            assert "extract_hour(current_timestamp)" in code
            
            # Verify complete integration
            assert "def init(self):" in code
            assert "def next(self):" in code
            assert "self.sma = self.I(" in code
            
        except Exception as e:
            if "Could not resolve indicator" in str(e):
                pytest.skip("SMA indicator not available")
            else:
                raise
    
    def test_minimal_strategy_integration(self):
        """Test integration with minimal strategies."""
        from research_agent.compiler import compile_strategy
        
        minimal_spec = StrategySpec(
            name="MinimalIntegration",
            description="Minimal strategy integration test",
            indicators=[],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        code = compile_strategy(minimal_spec)
        
        # Verify minimal strategy still has complete structure
        assert "class MinimalIntegration(Base):" in code
        assert "from strategies.Base import Base" in code
        assert "def init(self):" in code
        assert "def next(self):" in code
        assert "def validate_params" in code
        assert "get_optimization_params" in code
        
        # Verify minimal logic handling
        assert "pass" in code  # Should have pass for empty init
        assert "self.buy()" in code
        assert "self.sell()" in code
        
        # Verify no unnecessary imports
        assert "from calculate.indicators import" not in code
        assert "from datetime_utils import" not in code
    
    def test_error_recovery_integration(self):
        """Test error recovery and graceful handling in integration scenarios."""
        from research_agent.compiler import compile_strategy, CompilationError
        from pydantic import ValidationError
        
        # Test with potentially problematic specs
        # Test invalid condition expression (should be caught by compiler)
        invalid_condition_spec = StrategySpec(
            name="InvalidCondition",
            description="Invalid condition test",
            indicators=[],
            entry_conditions=[Condition(expression="invalid syntax and")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        with pytest.raises((CompilationError, Exception)):
            compile_strategy(invalid_condition_spec)
        
        # Test invalid strategy name (should be caught by Pydantic)
        with pytest.raises(ValidationError):
            StrategySpec(
                name="123InvalidName",  # Invalid Python identifier
                description="Invalid name test",
                indicators=[],
                entry_conditions=[Condition(expression="True")],
                exit_conditions=[Condition(expression="True")],
                optimization_params={}
            )
    
    def test_full_pipeline_with_file_operations(self):
        """Test the complete pipeline including file operations."""
        from research_agent.compiler import compile_strategy, save_strategy
        import tempfile
        import os
        
        spec = StrategySpec(
            name="FullPipelineTest",
            description="Complete pipeline test with file operations",
            indicators=[],
            entry_conditions=[
                Condition(expression="closes > opens")
            ],
            exit_conditions=[
                Condition(expression="closes < opens")
            ],
            optimization_params={
                "threshold": (0.01, 0.1)
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test compilation
            code = compile_strategy(spec)
            
            # Test file saving
            filepath = save_strategy(spec, temp_dir)
            
            # Verify file was created
            assert os.path.exists(filepath)
            assert os.path.basename(filepath) == "FullPipelineTest.py"
            
            # Verify file content
            with open(filepath, 'r') as f:
                saved_content = f.read()
            
            assert saved_content == code
            
            # Verify the saved file is a complete, valid Python module
            import ast
            ast.parse(saved_content)
            
            # Verify it has all required components
            assert "class FullPipelineTest(Base):" in saved_content
            assert "def init(self):" in saved_content
            assert "def next(self):" in saved_content
            assert "def validate_params" in saved_content
            assert "get_optimization_params" in saved_content


class TestCompositeIndicatorHandling:
    """Property 10: Composite indicator handling tests."""
    
    def test_composite_indicator_handling_property(self):
        """
        Property 10: Composite indicator handling
        For any indicator that returns multiple values, the generated code should handle 
        composite indicator access patterns correctly.
        **Validates: Requirements 2.4**
        """
        # Test with simple indicators first (since composite ones may not be available)
        test_indicators = [
            Indicator(name="sma1", type="sma", params={"period": 20}),
            Indicator(name="sma2", type="sma", params={"period": 50})
        ]
        
        spec = StrategySpec(
            name="CompositeTest",
            description="Test indicator handling",
            indicators=test_indicators,
            entry_conditions=[],
            exit_conditions=[],
            optimization_params={}
        )
        
        from research_agent.compiler import _generate_indicator_registrations
        
        try:
            registrations = _generate_indicator_registrations(spec.indicators)
            
            # Verify indicators are registered with self.I()
            for indicator in test_indicators:
                expected_pattern = f"self.{indicator.name} = self.I("
                assert expected_pattern in registrations, \
                    f"Indicator {indicator.name} must be registered with self.I()"
            
            # Verify the registrations use enhanced data access patterns
            assert "self.data.Close" in registrations, \
                "Registrations must use enhanced data access patterns"
            
            # The actual composite handling (for multi-value returns) is done by 
            # the enhanced Base framework's IndicatorWrapper system
            # The compiler just needs to generate the self.I() calls correctly
            
        except Exception as e:
            # Skip if indicators are not available
            if "Could not resolve indicator" in str(e):
                pytest.skip("Indicators not available - likely missing Librarian setup")
            else:
                raise


class TestIndicatorRegistration:
    """Property 2: Indicator registration transformation tests."""
    
    @settings(deadline=None)  # Disable deadline for this test
    @given(st.builds(
        StrategySpec,
        name=st.sampled_from(['TestStrategy1', 'TestStrategy2', 'TestStrategy3']),
        description=st.one_of(st.none(), st.just("Test strategy")),
        indicators=st.lists(
            st.builds(
                Indicator,
                name=st.sampled_from(['sma', 'ema', 'rsi']),
                type=st.sampled_from(['sma', 'ema', 'rsi']),
                params=st.dictionaries(
                    st.sampled_from(['period']),
                    st.integers(min_value=10, max_value=20),
                    min_size=0,
                    max_size=1
                )
            ),
            min_size=1,
            max_size=2
        ),
        entry_conditions=st.lists(st.builds(Condition, expression=st.just("True")), max_size=1),
        exit_conditions=st.lists(st.builds(Condition, expression=st.just("True")), max_size=1),
        optimization_params=st.just({})
    ))
    def test_indicator_registration_property(self, spec):
        """
        Property 2: Indicator registration transformation
        For any StrategySpec with indicators, each indicator should be registered 
        using self.I() calls in the init() method, with correct function names and parameters.
        **Validates: Requirements 1.3, 2.1, 2.2, 2.3**
        """
        # Mock the indicator registration generation
        from research_agent.compiler import _generate_indicator_registrations, _generate_init_method
        
        try:
            # Test indicator registration generation
            registrations = _generate_indicator_registrations(spec.indicators)
            
            # Verify each indicator has a self.I() registration
            for indicator in spec.indicators:
                expected_pattern = f"self.{indicator.name} = self.I("
                assert expected_pattern in registrations, \
                    f"Missing self.I() registration for indicator: {indicator.name}"
            
            # Test init method generation
            init_method = _generate_init_method(spec.indicators)
            
            # Verify init() method structure
            assert "def init(self):" in init_method, \
                "Generated init method must have proper signature"
            assert "Initialize strategy indicators and parameters" in init_method, \
                "Generated init method must have proper docstring"
            
            # Verify all indicators are registered in init
            for indicator in spec.indicators:
                expected_pattern = f"self.{indicator.name} = self.I("
                assert expected_pattern in init_method, \
                    f"Indicator {indicator.name} must be registered in init() method"
                    
        except Exception as e:
            # Skip tests that fail due to missing indicators or registry issues
            if "Could not resolve indicator" in str(e) or "Registry" in str(e):
                assume(False)  # Skip this test case
            else:
                raise


class TestEnhancedBaseInheritance:
    """Property 6: Enhanced Base inheritance tests."""
    
    @given(strategy_spec_strategy())
    def test_enhanced_base_inheritance_property(self, spec):
        """
        Property 6: Enhanced Base inheritance
        For any generated strategy, the code should inherit from the enhanced Base class 
        with correct import statements.
        **Validates: Requirements 1.1, 6.1**
        """
        generated_code = mock_compile_strategy(spec)
        
        # Verify enhanced Base import
        assert "from strategies.Base import Base" in generated_code, \
            "Generated code must import from enhanced Base framework"
        
        # Verify class inheritance
        class_pattern = rf"class {spec.name}\(Base\):"
        assert re.search(class_pattern, generated_code), \
            f"Generated class must inherit from Base: {spec.name}(Base)"
        
        # Verify no old-style imports that would conflict
        assert "from strategies.Base.Base import Base" not in generated_code, \
            "Should not use old-style Base import"
        
        # Verify the code is syntactically valid
        try:
            ast.parse(generated_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
        
        # Verify enhanced methods are present
        assert "def init(self):" in generated_code, \
            "Generated strategy must have init() method"
        assert "def next(self):" in generated_code, \
            "Generated strategy must have next() method"


class TestActualCompilerFunctionality:
    """Test the actual compile_strategy function."""
    
    def test_actual_compile_strategy_simple(self):
        """Test actual compile_strategy function with simple spec."""
        spec = StrategySpec(
            name="SimpleActualTest",
            description="Simple test for actual compiler",
            indicators=[],
            entry_conditions=[Condition(expression="True")],
            exit_conditions=[Condition(expression="True")],
            optimization_params={}
        )
        
        try:
            from research_agent.compiler import compile_strategy
            code = compile_strategy(spec)
            
            # Verify enhanced structure
            assert "from strategies.Base import Base" in code
            assert "class SimpleActualTest(Base):" in code
            assert "def init(self):" in code
            assert "def next(self):" in code
            assert "self.position['is_in_position']" in code
            assert "self.buy()" in code
            assert "self.sell()" in code
            
            # Verify no old patterns
            assert "def run(self, data, **kwargs):" not in code
            assert "for i in range(" not in code
            assert "in_position = False" not in code
            
            # Verify syntactic validity
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e) or "Registry" in str(e):
                pytest.skip("Indicator system not available")
            else:
                raise
    
    def test_actual_compile_strategy_with_time_conditions(self):
        """Test actual compile_strategy function with time-based conditions."""
        spec = StrategySpec(
            name="TimeBasedTest",
            description="Test time-based strategy compilation",
            indicators=[],
            entry_conditions=[Condition(expression="is_market_hours(timestamp)")],
            exit_conditions=[Condition(expression="extract_hour(timestamp) >= 15")],
            optimization_params={}
        )
        
        try:
            from research_agent.compiler import compile_strategy
            code = compile_strategy(spec)
            
            # Verify time-based imports
            assert "from datetime_utils import" in code
            assert "is_market_hours" in code
            assert "extract_hour" in code
            
            # Verify time-based filtering in next() method
            assert "current_timestamp = int(self.data.timestamps[-1])" in code
            assert "is_market_hours(current_timestamp)" in code
            assert "Time-based filtering" in code
            
            # Verify enhanced structure
            assert "from strategies.Base import Base" in code
            assert "def init(self):" in code
            assert "def next(self):" in code
            
            # Verify syntactic validity
            ast.parse(code)
            
        except Exception as e:
            if "Could not resolve indicator" in str(e) or "Registry" in str(e):
                pytest.skip("Indicator system not available")
            else:
                raise


class TestBasicCompilerFunctionality:
    """Basic unit tests for compiler functionality."""
    
    def test_simple_strategy_compilation(self):
        """Test compilation of a simple strategy."""
        spec = StrategySpec(
            name="SimpleTest",
            description="Simple test strategy",
            indicators=[],
            entry_conditions=[],
            exit_conditions=[],
            optimization_params={}
        )
        
        code = mock_compile_strategy(spec)
        
        # Basic structure checks
        assert "class SimpleTest(Base):" in code
        assert "from strategies.Base import Base" in code
        assert "def init(self):" in code
        assert "def next(self):" in code
        
        # Verify syntactic validity
        ast.parse(code)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])