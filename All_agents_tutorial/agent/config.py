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
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_llm_model = "openai/gpt-oss-120b"
        self.max_steps = 6
        self.max_tool_calls = 5
        self.cache_ttl_seconds = 3600
        # self.llm_provider = "gemini"
        self.llm_provider = "groq"
        self.temperature = 0.1
        self.top_p = 0.9
        self.max_sql_errors = 2
        self.max_context_messages = 12
        self.recent_messages_to_keep = 6
        self.max_objective_characters = 4000
        self.max_final_report_characters = 6000
        self.sql_cache_ttl_seconds = 300

        self.cache_backend = os.getenv("CACHE_BACKEND", "memory").lower()
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.cache_namespace = os.getenv(
            "CACHE_NAMESPACE",
            "self-driving-analyst",
        )

        self.sql_cache_lock_ttl_seconds = 30
        self.sql_cache_wait_seconds = 1.0
        self.sql_cache_poll_interval_seconds = 0.05

        self.celery_broker_url = os.getenv(
            "CELERY_BROKER_URL",
            "redis://localhost:6379/1",
        )

        self.app_database_path = DATA_DIRECTORY / "data" / "app_database.sqlite3"

        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set")    


setting = Settings()
