import sqlite3 
from contextlib import contextmanager
from agent.config import setting



def initialize_database() -> None:
    with sqlite3.connect(setting.app_database_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS investigation_runs (
                run_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                objective TEXT NOT NULL,
                status TEXT NOT NULL,
                final_report TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id)
                    REFERENCES investigation_runs(run_id)
            )
        """)

        connection.commit()


@contextmanager
def get_app_database():
    connection = sqlite3.connect(setting.app_database_path)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()       
    
    