"""
Strategy Compiler

Transforms a StrategySpec (JSON) into a valid Python strategy class.
This is a DETERMINISTIC, SANDBOXED component - no LLM involvement.
"""

from research_agent.schema import StrategySpec, Indicator, IndicatorType
from typing import Dict, Optional
from research_agent.tools import write_file
from research_agent.librarian import add_indicator
import importlib
import sys

# Dynamic Import Wrapper
def get_indicator_function_name(name: str) -> Optional[str]:
    """
    Dynamically resolve indicator function name.
    If missing, trigger Librarian to create it.
    Returns the valid function name (e.g. 'calculate_sma') or None.
    """
    func_name = f"calculate_{name}"
    
    def try_import():
        try:
            # Force reload of the package and its submodules
            # This is expensive but necessary for "hot-loading" new indicators
            if "calculate.indicators" in sys.modules:
                importlib.reload(sys.modules["calculate.indicators"])
                # Also reload submodules (trend, momentum, etc)
                for mod_name in list(sys.modules.keys()):
                    if mod_name.startswith("calculate.indicators."):
                        importlib.reload(sys.modules[mod_name])
            else:
                importlib.import_module("calculate.indicators")
                
            module = sys.modules["calculate.indicators"]
            return hasattr(module, func_name)
        except ImportError:
            return False

    if try_import():
        return func_name
    
    # Not found -> Invoke Librarian
    print(f"⚠️ Indicator '{name}' not found. Invoking Librarian...")
    try:
        success = add_indicator(name)
        if success:
            if try_import():
                print(f"new indicator function '{func_name}' added successfully")
                return func_name
    except Exception as e:
        print(f"Librarian error: {e}")
        
    return None


def _generate_indicator_calls(indicators: list[Indicator]) -> str:
    """Generate indicator calculation calls."""
    lines = []
    
    for ind in indicators:
        # 1. Ensure it exists (Trigger Librarian side-effect)
        fn_name = get_indicator_function_name(ind.type)
        if not fn_name:
            print(f"❌ Could not resolve indicator: {ind.type}")
            continue

        params = ind.params
        
        # 2. Generate Call Code
        # We use known patterns for standard indicators, and a generic fallback for new ones.
        
        args = ""
        # Standard Signatures
        match ind.type:
            case IndicatorType.SMA | IndicatorType.EMA | IndicatorType.RSI:
                args = f"closes, {params.get('period', 14)}"
            case IndicatorType.ATR | IndicatorType.ADX | "keltner": # Example of new ones
                args = f"highs, lows, closes, {params.get('period', 14)}"
            case IndicatorType.BOLLINGER:
                args = f"closes, {params.get('period', 20)}, {params.get('std_dev', 2)}"
            case IndicatorType.VWAP:
                args = "highs, lows, closes, volume"
            case IndicatorType.SUPERTREND:
                args = f"highs, lows, closes, {params.get('period', 10)}, {params.get('multiplier', 3.0)}"
            case IndicatorType.MACD:
                args = f"closes, {params.get('fast', 12)}, {params.get('slow', 26)}, {params.get('signal', 9)}"
            case _:
                # Generic Fallback for unknown/new indicators
                # Heuristic: if 'period' in params, pass it.
                if 'period' in params:
                    args = f"closes, {params['period']}"
                else:
                    args = "closes"

        # Return unpacking
        # PHASE 3 UPDATE: We use NamedTuples (or Objects) for composite indicators.
        # So we do NOT unpack them here. We assign the result to the indicator name.
        # The strategy logic (via Dot Notation) determines access.
        
        # Default Assignment
        lines.append(f"        {ind.name} = {fn_name}({args})")

    return "\n".join(lines)


def _generate_entry_logic(conditions: list) -> str:
    """Generate entry condition logic."""
    if not conditions:
        return "False"
    exprs = [f"({c.expression})" for c in conditions]
    return " and ".join(exprs)


def _generate_exit_logic(conditions: list) -> str:
    """Generate exit condition logic."""
    if not conditions:
        return "False"
    exprs = [f"({c.expression})" for c in conditions]
    return " or ".join(exprs)


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
    Compile a StrategySpec into executable Python code.
    """
    
    # Collect imports needed
    imports = []
    needed_funcs = set()
    for ind in spec.indicators:
        fn_name = f"calculate_{ind.type}"
        # We assume _generate_indicator_calls has run or will run, 
        # but better to just import what we expect. 
        # The dynamic loader ensures they exist.
        needed_funcs.add(fn_name)
    
    if needed_funcs:
        imports.append(f"from calculate.indicators import {', '.join(sorted(needed_funcs))}")
    
    indicator_imports_str = "\n".join(imports)
    
    indicator_calls = _generate_indicator_calls(spec.indicators)
    entry_logic = _generate_entry_logic(spec.entry_conditions)
    exit_logic = _generate_exit_logic(spec.exit_conditions)
    opt_params = _generate_optimization_params(spec.optimization_params)
    
    # Generate the full class
    code = f'''"""
Auto-generated strategy: {spec.name}
{spec.description or 'No description provided.'}
"""

from strategies.Base import Base
import numpy as np
from numba import njit
{indicator_imports_str}

class {spec.name}(Base):
    """
    {spec.description or spec.name}
    """
    
    def run(self, data, **kwargs):
        symbol, dates, times, opens, highs, lows, closes, volume = data
        
        n = len(closes)
        returns = np.zeros(n)
        
        # Calculate indicators
{indicator_calls}
        
        # Trading logic
        in_position = False
        entry_price = 0.0
        
        # Determine start index (need enough data for indicators)
        start_idx = 50  # Safe default, adjust based on longest indicator period
        
        for i in range(start_idx, n):
            # Entry
            if not in_position:
                try:
                    if {entry_logic}:
                        in_position = True
                        entry_price = closes[i]
                except:
                    pass
            
            # Exit
            elif in_position:
                try:
                    if {exit_logic}:
                        in_position = False
                        exit_price = closes[i]
                        returns[i] = (exit_price - entry_price) / entry_price
                except:
                    pass
        
        return returns
    
    def validate_params(self, **kwargs) -> bool:
        # Auto-generated: no custom validation
        return True
    
    @staticmethod
    def get_optimization_params():
{opt_params}
'''
    return code


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
