"""
Strategy Compiler

Transforms a StrategySpec (JSON) into a valid Python strategy class.
This is a DETERMINISTIC, SANDBOXED component - no LLM involvement.
"""

from research_agent.schema import StrategySpec, Indicator, IndicatorType
from typing import Dict
from research_agent.tools import write_file


# Indicator code generators
INDICATOR_TEMPLATES: Dict[IndicatorType, str] = {
    IndicatorType.SMA: """
def calc_{name}(closes, period):
    sma = np.full(len(closes), np.nan)
    for i in range(period - 1, len(closes)):
        sma[i] = np.mean(closes[i - period + 1:i + 1])
    return sma
""",
    IndicatorType.EMA: """
def calc_{name}(closes, period):
    ema = np.full(len(closes), np.nan)
    multiplier = 2 / (period + 1)
    ema[period - 1] = np.mean(closes[:period])
    for i in range(period, len(closes)):
        ema[i] = (closes[i] - ema[i - 1]) * multiplier + ema[i - 1]
    return ema
""",
    IndicatorType.RSI: """
def calc_{name}(closes, period):
    n = len(closes)
    rsi = np.full(n, np.nan)
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    for i in range(period, n - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi[i + 1] = 100 - (100 / (1 + rs))
    return rsi
""",
    IndicatorType.ATR: """
def calc_{name}(highs, lows, closes, period):
    n = len(closes)
    atr = np.full(n, np.nan)
    tr = np.zeros(n)
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)
    atr[period] = np.mean(tr[1:period + 1])
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr
""",
    IndicatorType.BOLLINGER: """
def calc_{name}(closes, period, std_dev=2):
    n = len(closes)
    middle = np.full(n, np.nan)
    upper = np.full(n, np.nan)
    lower = np.full(n, np.nan)
    for i in range(period - 1, n):
        window = closes[i - period + 1:i + 1]
        m = np.mean(window)
        s = np.std(window)
        middle[i] = m
        upper[i] = m + std_dev * s
        lower[i] = m - std_dev * s
    return middle, upper, lower
""",
}


def _generate_indicator_calls(indicators: list[Indicator]) -> str:
    """Generate indicator calculation calls."""
    lines = []
    for ind in indicators:
        params = ind.params
        if ind.type == IndicatorType.SMA:
            lines.append(f"        {ind.name} = calc_{ind.name}(closes, {params.get('period', 20)})")
        elif ind.type == IndicatorType.EMA:
            lines.append(f"        {ind.name} = calc_{ind.name}(closes, {params.get('period', 20)})")
        elif ind.type == IndicatorType.RSI:
            lines.append(f"        {ind.name} = calc_{ind.name}(closes, {params.get('period', 14)})")
        elif ind.type == IndicatorType.ATR:
            lines.append(f"        {ind.name} = calc_{ind.name}(highs, lows, closes, {params.get('period', 14)})")
        elif ind.type == IndicatorType.BOLLINGER:
            lines.append(f"        {ind.name}_middle, {ind.name}_upper, {ind.name}_lower = calc_{ind.name}(closes, {params.get('period', 20)}, {params.get('std_dev', 2)})")
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
    
    # Collect unique indicator function definitions
    indicator_funcs = []
    for ind in spec.indicators:
        template = INDICATOR_TEMPLATES.get(ind.type)
        if template:
            indicator_funcs.append(template.format(name=ind.name))
    
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

# Indicator Functions
{chr(10).join(indicator_funcs)}

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
