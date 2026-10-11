from agent.config import setting
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory


def get_llm():
    if setting.llm_provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=setting.llm_model,
            api_key=setting.gemini_api_key,
            temperature=setting.temperature,
            top_p=setting.top_p,
        )
    raise ValueError(f"LLM Provider {setting.llm_provider} not found")
        


msg = get_llm().invoke("hi")
print(msg)
print("helloworld")