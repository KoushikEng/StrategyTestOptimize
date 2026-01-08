"""
Strategy Translator Agent

Converts natural language or PineScript descriptions into a formal StrategySpec.
This is where the LLM is used.
"""

import os
import json
from typing import Optional
from research_agent.schema import StrategySpec, Indicator, Condition, IndicatorType


# System prompt for the Translator LLM
TRANSLATOR_SYSTEM_PROMPT = """You are a trading strategy translator. Your job is to convert natural language or PineScript descriptions into a JSON specification.

## Output Format
You MUST output ONLY valid JSON conforming to this schema:
{
  "name": "StrategyName",  // PascalCase, valid Python class name
  "description": "Brief description",
  "indicators": [
    {"name": "indicator_id", "type": "indicator_type", "params": {"period": 14}}
  ],
  "entry_conditions": [
    {"expression": "indicator_id[i] < 30", "description": "Entry when..."}
  ],
  "exit_conditions": [
    {"expression": "indicator_id[i] > 70", "description": "Exit when..."}
  ],
  "position_type": "long",  // or "short" or "both"
  "optimization_params": {
    "param_name": [min_value, max_value]
  }
}

## Supported Indicators (use EXACTLY these type values)
- "sma" (Simple Moving Average) - params: period
- "ema" (Exponential Moving Average) - params: period  
- "rsi" (Relative Strength Index) - params: period
- "atr" (Average True Range) - params: period
- "bollinger" (Bollinger Bands) - params: period, std_dev

## Expression Syntax
- Use [i] to index the current bar, e.g., "rsi[i] < 30"
- Use Python comparison operators: <, >, <=, >=, ==, !=
- For crossovers: "fast_ema[i] > slow_ema[i] and fast_ema[i-1] <= slow_ema[i-1]"

## Rules
1. Extract the LOGIC, not the exact code
2. Map to supported indicators only
3. Keep it simple - no complex nested logic
4. Always provide optimization bounds for tunable parameters

Output ONLY the JSON, no explanation or markdown."""


def translate_with_openai(description: str, api_key: Optional[str] = None) -> StrategySpec:
    """
    Translate description to StrategySpec using OpenAI API.
    """
    import openai
    
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    client = openai.OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": TRANSLATOR_SYSTEM_PROMPT},
            {"role": "user", "content": f"Convert this strategy to JSON:\n\n{description}"}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    json_str = response.choices[0].message.content
    spec_dict = json.loads(json_str)
    
    return StrategySpec(**spec_dict)


def translate_with_google(description: str, api_key: Optional[str] = None) -> StrategySpec:
    """
    Translate description to StrategySpec using Google Gemini API.
    """
    import google.generativeai as genai
    
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Google API key not found. Set GOOGLE_API_KEY environment variable.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = f"{TRANSLATOR_SYSTEM_PROMPT}\n\nConvert this strategy to JSON:\n\n{description}"
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    
    json_str = response.text
    spec_dict = json.loads(json_str)
    
    return StrategySpec(**spec_dict)


def translate(description: str, provider: str = "google", api_key: Optional[str] = None) -> StrategySpec:
    """
    Translate a natural language or PineScript description to StrategySpec.
    
    Args:
        description: The strategy description
        provider: LLM provider ("openai" or "google")
        api_key: Optional API key (falls back to environment variable)
        
    Returns:
        StrategySpec: The parsed strategy specification
    """
    if provider == "openai":
        return translate_with_openai(description, api_key)
    elif provider == "google":
        return translate_with_google(description, api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# Example / Testing
if __name__ == "__main__":
    # Test with a simple description
    test_description = """
    Create a mean reversion strategy using RSI.
    Buy when RSI is below 30 (oversold).
    Sell when RSI goes above 70 (overbought).
    Use a 14 period RSI.
    """
    
    print("Testing Translator Agent...")
    print(f"Input: {test_description}")
    print()
    
    try:
        spec = translate(test_description, provider="google")
        print("Generated Spec:")
        print(spec.model_dump_json(indent=2))
    except Exception as e:
        print(f"Translation failed: {e}")
        print("Make sure GOOGLE_API_KEY environment variable is set.")
