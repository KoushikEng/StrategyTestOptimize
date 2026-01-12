from langchain_google_genai import ChatGoogleGenerativeAI
from research_agent.config import GEMINI_MODEL, GEMINI_TEMP, GEMINI_API_KEY


llm = None

try:
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=GEMINI_TEMP,
        api_key=GEMINI_API_KEY
    )
except Exception as e:
    raise ValueError(f"❌ Failed to initialize Gemini LLM: {e}")
