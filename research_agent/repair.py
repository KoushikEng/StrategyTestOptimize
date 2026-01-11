"""
Repair Agent

Analyzes errors or negative feedback and attempts to fix the StrategySpec.
Uses LangChain for model abstraction.
"""

import os
from typing import Optional, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from research_agent.schema import StrategySpec

REPAIR_SYSTEM_TEMPLATE = """You are a Strategy Repair Agent. 
Your job is to FIX a trading strategy specification based on an error message or review feedback.

You will receive:
1. The current Strategy Spec (JSON).
2. The Error or Feedback.

## Goal
Output a CORRECTED JSON Strategy Spec.
- If it's a syntax error, fix the JSON or Logic.
- If it's an "Unknown Indicator" error, replace it with a standard one or remove it.
- If it's a "Review Rejection" (e.g. "Too few trades"), relax the entry conditions.
- If it's a "100% Win Rate" (Data Leak), try to shift logic to prevent lookahead.

{format_instructions}
"""

def get_llm(provider: str, api_key: Optional[str] = None):
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o", 
            temperature=0.2,
            api_key=api_key or os.environ.get("OPENAI_API_KEY")
        )
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            api_key=api_key or os.environ.get("GOOGLE_API_KEY")
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


def repair_spec(
    current_spec: Dict,
    error_context: str,
    provider: str = "google",
    api_key: Optional[str] = None
) -> Dict:
    """
    Repair a strategy spec based on error context using LangChain.
    """
    llm = get_llm(provider, api_key)
    
    parser = JsonOutputParser(pydantic_object=StrategySpec)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", REPAIR_SYSTEM_TEMPLATE),
        ("user", "CURRENT SPEC:\n{spec}\n\nISSUE TO FIX:\n{error}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "spec": str(current_spec),
            "error": error_context,
            "format_instructions": parser.get_format_instructions()
        })
        # Return dict directly as master/nodes expects dict/schema compatibility
        return result
    except Exception as e:
        raise ValueError(f"Repair failed: {str(e)}")


if __name__ == "__main__":
    # Test
    broken_spec = {
        "name": "BadStrat",
        "indicators": [],
        "entry_conditions": [{"expression": "unknown > 0"}], 
        "exit_conditions": []
    }
    print("Testing Repair (LangChain)...")
    try:
        fixed = repair_spec(broken_spec, "Error: Unknown variable 'unknown'")
        print("Fixed:")
        print(fixed)
    except Exception as e:
        print(f"Error: {e}")
