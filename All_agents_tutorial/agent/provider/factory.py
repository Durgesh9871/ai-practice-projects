from agent.config import setting
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


def get_llm():
    if setting.llm_provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=setting.llm_model,
            api_key=setting.gemini_api_key,
            temperature=setting.temperature,
        )
    elif setting.llm_provider == "groq":
        return ChatGroq(
            model=setting.groq_llm_model,
            api_key=setting.groq_api_key,
            temperature=setting.temperature,
        )

    raise ValueError(f"LLM Provider {setting.llm_provider} not found")
        


