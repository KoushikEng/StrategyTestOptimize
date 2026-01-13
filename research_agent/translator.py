"""
Strategy Translator Agent

Converts natural language or PineScript descriptions into a formal StrategySpec.
Uses LangChain for model abstraction and output parsing.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from research_agent.schema import StrategySpec
from research_agent.tools import write_file
from research_agent.llm import llm

# Define the Pydantic wrapper for LangChain parser if needed, 
# or just use the existing StrategySpec directly if compatible.
# StrategySpec uses standard Pydantic, but langchain might prefer v1 depending on version.
# Given we installed langchain-core, it likely uses v1 or v2 bridge.
# Let's try direct usage first.

SYSTEM_TEMPLATE = """You are a trading strategy translator. Your job is to convert natural language or PineScript descriptions into a JSON specification.

## Output Format
You MUST output ONLY valid JSON conforming to the StrategySpec schema.

## Expression Syntax
- Use [i] to index the current bar, e.g., "rsi[i] < 30"
- Use Python comparison operators: <, >, <=, >=, ==, !=
- For crossovers: "fast_ema[i] > slow_ema[i] and fast_ema[i-1] <= slow_ema[i-1]"

## Composite Indicators (CRITICAL)
- Treat composite indicators (e.g., Ichimoku, Bollinger, MACD, etc.) as **SINGLE** entries in the `indicators` list.
- Use generic types: `type="ichimoku"`, `type="bollinger"`, `type="stoch"`.
- Do NOT split them (e.g., do NOT use `ichimoku_tenkan`).
- **Access Components via Dot Notation**:
    -   Ichimoku ($name="cloud"$): `cloud.tenkan[i]`, `cloud.kijun[i]`, `cloud.senkou_a[i]`, `cloud.senkou_b[i]`
    -   Bollinger ($name="bb"$): `bb.upper[i]`, `bb.middle[i]`, `bb.lower[i]`
    -   MACD ($name="macd"$): `macd.macd[i]`, `macd.signal[i]`, `macd.hist[i]`
    -   ADX ($name="adx"$): `adx.adx[i]`, `adx.pdi[i]`, `adx.mdi[i]`

## Rules
1. Extract the LOGIC, not the exact code.
2. Keep it simple - no complex nested logic.
3. Always provide optimization bounds for tunable parameters.

{format_instructions}
"""


def translate(description: str) -> StrategySpec:
    """
    Translate description to StrategySpec using LangChain.
    """
    parser = JsonOutputParser(pydantic_object=StrategySpec)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        ("user", "Convert this strategy to JSON:\n\n{description}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "description": description,
            "format_instructions": parser.get_format_instructions()
        })
        # Result is a dict, convert to Spec
        return StrategySpec(**result)
    except Exception as e:
        # Fallback or specific error handling
        raise ValueError(f"Translation failed: {str(e)}")
    
def save_spec(spec: StrategySpec) -> int:
    """
    Save the strategy spec to a file.
    """
    return write_file(f"research_agent/runs/specs/{spec.name}.json", spec.model_dump_json(indent=2))


if __name__ == "__main__":
    # Test
    desc = "Buy when RSI < 30, sell when RSI > 70. Use 14 period."
    print("Testing Translator (LangChain)...")
    try:
        spec = translate(desc)
        print("Success:")
        print(spec.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error: {e}")
