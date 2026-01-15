"""
Librarian Agent (Indicator Adder)

Responsible for extending the system's capabilities by implementing missing
technical indicators and adding them to the standard library.
"""

import os
import re
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from research_agent.llm import llm
from research_agent.tools import write_file
from research_agent.indicator_registry import register_indicator


def _register_from_code(name: str, code: str) -> None:
    """
    Parse the SIGNATURE comment from generated code and register it.
    Expected format: # SIGNATURE: args=["closes"] defaults={"period": 14}
    """
    # Try to find the signature comment
    match = re.search(r'# SIGNATURE:\s*args=(\[.*?\])\s*defaults=(\{.*?\})', code)
    if match:
        try:
            args = eval(match.group(1))  # Safe: we control the LLM output format
            defaults = eval(match.group(2))
            register_indicator(name, args, defaults)
            print(f"📝 Registered signature for '{name}': args={args}, defaults={defaults}")
        except Exception as e:
            print(f"⚠️ Could not parse signature for '{name}': {e}")
            # Fallback: register with generic signature
            register_indicator(name, ["closes"], {"period": 14})
    else:
        # No signature found, use heuristic
        print(f"⚠️ No SIGNATURE comment found for '{name}', using generic signature")
        register_indicator(name, ["closes"], {"period": 14})

# Mapping categories to files
CATEGORY_FILES = {
    "trend": "calculate/indicators/trend.py",
    "momentum": "calculate/indicators/momentum.py",
    "volatility": "calculate/indicators/volatility.py",
    "volume": "calculate/indicators/volume.py",
    "other": "calculate/indicators/other.py" # Fallback
}

CODE_GEN_TEMPLATE = """You are an expert Python Quantitative Developer specializing in Numba optimization.
Your task is to implement a Technical Indicator function.

Indicator Name: {name}

## Requirements
1.  **Numba Optimized**: Decorate with `@njit`.
2.  **Do not add any imports**:
    -   Assume `import numpy as np`, `from numba import njit` and `from collections import namedtuple` are already present in the file.
    -   **Reuse Primitives**: IF you need SMA, EMA, ATR, or Rolling Std:
        Assume these functions are already imported in the file:
        `calculate_sma, calculate_ema, calculate_atr, _calculate_rolling_std`
    -   Do NOT reimplement these primitives.
3.  **Outputs**:
    -   If the indicator returns a single array, return `np.ndarray`.
    -   If it returns MULTIPLE arrays (e.g., Bollinger, Ichimoku), you MUST return a `collections.namedtuple`.
    -   Since `numba.njit` supports namedtuples, define it *outside* the function.
    -   Example:
        ```python
        BbandsResult = namedtuple('BbandsResult', ['middle', 'upper', 'lower'])
        
        @njit
        def calculate_bollinger(...):
            ...
            return BbandsResult(mid, up, low)
        ```
    -   **Ichimoku Components**: tenkan, kijun, senkou_a, senkou_b, chikou.
4.  **No Pandas**: Use purely `numpy` arrays.
5.  **Style**: PEP8.

## Output Format
Return ONLY the Python code (namedtuple definition + function).
Function name MUST be `calculate_{name}`.

## CRITICAL: Place a SIGNATURE comment on the FIRST LINE inside the function (before the docstring):
```python
@njit
def calculate_example(closes, period=14):
    # SIGNATURE: args=["closes"] defaults={{"period": 14}}
    \"\"\"
    Docstring here...
    \"\"\"
    ...
```
-   args = list of positional data arrays your function needs (e.g., ["highs", "lows", "closes", "volume"])
-   defaults = dict of keyword parameters with their default values (e.g., {{"period": 14, "num_std": 2.0}})
-   This MUST be the first line after `def ...:` and BEFORE the docstring.
"""

CLASSIFY_TEMPLATE = """Classify the technical indicator '{name}' into one of these categories:
- trend
- momentum
- volatility
- volume
- other

Return ONLY the category name.
"""

def classify_indicator(name: str) -> str:
    """Determine the category of an indicator."""
    prompt = ChatPromptTemplate.from_template(CLASSIFY_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    
    category = chain.invoke({"name": name}).strip().lower()
    return category if category in CATEGORY_FILES else "other"

def generate_indicator_code(name: str) -> str:
    """Generate the Numba code for an indicator."""
    prompt = ChatPromptTemplate.from_template(CODE_GEN_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    
    code = chain.invoke({"name": name})
    # Clean markdown if present
    code = re.sub(r"```python\n|```", "", code).strip()
    return code

def update_init(name: str, category: str) -> None:
    """
    Append the indicator to the __init__.py file.
    """
    func_name = "calculate_" + name
    init_file = "calculate/indicators/__init__.py"
    
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write(f"from .{category} import {func_name}\n")
        return

    try:
        with open(init_file, "r+") as f:
            content = f.read()

            pattern = rf"^from \.{category} import (.*)$"
            match = re.search(pattern, content, re.MULTILINE)
            
            if not match:
                f.write(f"\nfrom .{category} import {func_name}\n")
                return
            
            match_line = match.group()
            existing_func_names = match.group(1).strip()

            if func_name in [n.strip() for n in existing_func_names.split(",")]:
                # already exists
                return
            
            replace_line = f"{match_line}, {func_name}"
            content = re.sub(pattern, replace_line, content, 1, re.MULTILINE)
            
            f.seek(0)
            f.write(content)
            f.truncate()
    except Exception as e:
        print(f"Error updating __init__.py: {e}")

def add_indicator(name: str) -> Optional[None]:
    """
    Main entry point: Generates and saves a new indicator.
    """
    print(f"📚 Librarian: Adding new indicator '{name}'...")
    
    # GUARDRAIL: Do not re-implement primitives that exist in core
    if name.lower() in ["sma", "ema", "atr"]:
        print(f"⚠️  Librarian: '{name}' is a primitive in calculate.indicators.core. Skipping generation.")
        return "core"
    
    try:
        # 1. Classify
        category = classify_indicator(name)
        target_file = CATEGORY_FILES.get(category, "calculate/indicators/other.py")
        
        # 2. Generate Code
        code = generate_indicator_code(name)
        
        # 3. Save to File
        # Ensure target file exists (if 'other.py')
        if not os.path.exists(target_file):
            write_file(target_file, '"""Other Indicators"""\nimport numpy as np\nfrom numba import njit\n\n')
            
        with open(target_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n{code}\n")
            
        # 4. Update __init__.py
        update_init(name, category)
        
        # 5. Register signature in the registry
        _register_from_code(name, code)
            
        print(f"✅ Librarian: Added 'calculate_{name}' to {target_file}")
        return category
        
    except Exception as e:
        print(f"❌ Librarian Failed: {e}")
        return None

if __name__ == "__main__":
    # Test
    print("Testing Librarian...")
    # Mocking or requiring API key
    # add_indicator("keltner_channel")
    pass
