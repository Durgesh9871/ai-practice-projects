from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv()

DATA_DIRECTORY = Path(__file__).resolve().parent.parent

# print(DATA_DIRECTORY)


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.llm_model = "gemini-3.6-flash"
        self.max_steps = 6
        self.max_tool_calls = 5
        self.cache_ttl_seconds = 3600
        self.llm_provider = "gemini"
        self.temperature = 0.1
        self.top_p = 0.9
        self.max_sql_errors = 2
        self.max_context_messages = 12
        self.recent_messages_to_keep = 6
        self.max_objective_characters = 4000

        self.app_database_path = DATA_DIRECTORY / "data" / "app_database.sqlite3"

        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set")    


setting = Settings()
