from langchain_openai import ChatOpenAI
from research_agent.config import LLM_MODEL, LLM_TEMP, OPENROUTER_API_KEY


llm = None

try:
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",  # OpenRouter base URL
        model=LLM_MODEL,
        temperature=LLM_TEMP,
        api_key=OPENROUTER_API_KEY
    )
except Exception as e:
    raise ValueError(f"❌ Failed to initialize LLM: {e}")
