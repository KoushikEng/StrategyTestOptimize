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
2.  **Inputs**: Typically `(closes, period)` or `(highs, lows, closes, period)`.
3.  **Outputs**: A numpy array of the same length as input, or a tuple of arrays.
4.  **No Pandas**: Use purely `numpy` arrays.
5.  **Imports**: Assume `import numpy as np` and `from numba import njit` are already present in the file.
6.  **Style**: PEP8.

## Output Format
Return ONLY the Python function code. No markdown formatting.
Function name MUST be `calculate_{name}`.
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

def add_indicator(name: str) -> bool:
    """
    Main entry point: Generates and saves a new indicator.
    """
    print(f"📚 Librarian: Adding new indicator '{name}'...")
    
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
        init_file = "calculate/indicators/__init__.py"
        with open(init_file, "a", encoding="utf-8") as f:
            f.write(f"\nfrom .{category} import calculate_{name}")
            
        print(f"✅ Librarian: Added 'calculate_{name}' to {target_file}")
        return True
        
    except Exception as e:
        print(f"❌ Librarian Failed: {e}")
        return False

if __name__ == "__main__":
    # Test
    print("Testing Librarian...")
    # Mocking or requiring API key
    # add_indicator("keltner_channel")
    pass
