from agent.config import setting
from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm():
    if setting.llm_provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=setting.llm_model,
            api_key=setting.gemini_api_key,
            temperature=setting.temperature,
        )
    raise ValueError(f"LLM Provider {setting.llm_provider} not found")
        


