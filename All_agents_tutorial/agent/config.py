from dotenv import load_dotenv
import os
load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.llm_model = "gemini-3.6-flash"
        self.max_steps = 5
        self.max_tool_calls = 5
        self.cache_ttl_seconds = 3600
        self.llm_provider = "gemini"
        self.temperature = 0.1
        self.top_p = 0.9

        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set")    


setting = Settings()
