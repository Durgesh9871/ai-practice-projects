import duckdb
from data.loader import DB_PATH
from collections.abc import Generator


def get_analytics_connection() -> Generator:
    conn = duckdb.connect(str(DB_PATH))
 
    try:
        yield conn
    finally:
        conn.close()

    
