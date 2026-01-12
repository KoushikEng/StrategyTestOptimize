"""
Strategy Compiler

Transforms a StrategySpec (JSON) into a valid Python strategy class.
This is a DETERMINISTIC, SANDBOXED component - no LLM involvement.
"""

from research_agent.schema import StrategySpec, Indicator, IndicatorType
from typing import Dict
from research_agent.tools import write_file


# Indicator code generators
# Indicator Import Mapping
# Maps IndicatorType to the function name in calculate.indicators
INDICATOR_IMPORTS: Dict[IndicatorType, str] = {
    IndicatorType.SMA: "calculate_sma",
    IndicatorType.EMA: "calculate_ema",
    IndicatorType.RSI: "calculate_rsi",
    IndicatorType.MACD: "calculate_macd",
    IndicatorType.ATR: "calculate_atr",
    IndicatorType.BOLLINGER: "calculate_bollinger_bands",
    IndicatorType.VWAP: "calculate_vwap",
    IndicatorType.ADX: "calculate_adx",
    IndicatorType.SUPERTREND: "calculate_supertrend",
}


def _generate_indicator_calls(indicators: list[Indicator]) -> str:
    """Generate indicator calculation calls."""
    lines = []
    for ind in indicators:
        params = ind.params
        fn_name = INDICATOR_IMPORTS.get(ind.type)
        if not fn_name:
            # Fallback or error? For now, skip unknown
            continue

        # Generate Call based on signature known conventions
        match ind.type:
            case IndicatorType.SMA:
                lines.append(f"        {ind.name} = calculate_sma(closes, {params.get('period', 20)})")
            case IndicatorType.EMA:
                lines.append(f"        {ind.name} = calculate_ema(closes, {params.get('period', 20)})")
            case IndicatorType.RSI:
                lines.append(f"        {ind.name} = calculate_rsi(closes, {params.get('period', 14)})")
            case IndicatorType.ATR:
                lines.append(f"        {ind.name} = calculate_atr(highs, lows, closes, {params.get('period', 14)})")
            case IndicatorType.BOLLINGER:
                lines.append(f"        {ind.name}_mid, {ind.name}_up, {ind.name}_low = calculate_bollinger_bands(closes, {params.get('period', 20)}, {params.get('std_dev', 2)})")
            case IndicatorType.ADX:
                lines.append(f"        {ind.name}, {ind.name}_pdi, {ind.name}_mdi = calculate_adx(highs, lows, closes, {params.get('period', 14)})")
            case IndicatorType.SUPERTREND:
                lines.append(f"        {ind.name} = calculate_supertrend(highs, lows, closes, {params.get('period', 10)}, {params.get('multiplier', 3.0)})")
            case IndicatorType.MACD:
                lines.append(f"        {ind.name}, {ind.name}_sig, {ind.name}_hist = calculate_macd(closes, {params.get('fast', 12)}, {params.get('slow', 26)}, {params.get('signal', 9)})")
            case IndicatorType.VWAP:
                lines.append(f"        {ind.name} = calculate_vwap(highs, lows, closes, volume)")

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
    
    Args:
        spec: The strategy specification
        
    Returns:
        str: Valid Python code for the strategy class
    """
    
    # Collect imports needed
    imports = []
    needed_funcs = set()
    for ind in spec.indicators:
        fn_name = INDICATOR_IMPORTS.get(ind.type)
        if fn_name:
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
    
    Args:
        spec: The strategy specification
        output_dir: Directory to save the file
        
    Returns:
        str: Path to the saved file
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
    from research_agent.schema import StrategySpec, Indicator, Condition, IndicatorType
    
    # Create a test spec
    test_spec = StrategySpec(
        name="TestRsiStrategy",
        description="Buy when RSI < 30, sell when RSI > 70",
        indicators=[
            Indicator(name="rsi", type=IndicatorType.RSI, params={"period": 14})
        ],
        entry_conditions=[
            Condition(expression="rsi[i] < 30", description="RSI oversold")
        ],
        exit_conditions=[
            Condition(expression="rsi[i] > 70", description="RSI overbought")
        ],
        optimization_params={
            "rsi_period": (7, 21)
        }
    )
    
    # Compile
    code = compile_strategy(test_spec)
    print("Generated Code:")
    print("=" * 60)
    print(code)
    
    # Save
    path = save_strategy(test_spec)
    print(f"\nSaved to: {path}")
