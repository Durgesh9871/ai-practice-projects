import hashlib
from typing import Any
from agent.sql_utils import normalize_sql


def make_sql_cache_key(query: str) -> str:
    """Create a cache key from function arguments."""
    normalized_query = normalize_sql(query)

    digest = hashlib.sha256(normalized_query.encode('utf-8')).hexdigest()
    return f"sql-result:{digest}"



def is_cacheable_sql(query: str) -> bool:
    volatile_words = {
        "CURRENT_TIMESTAMP",
        "CURRENT_DATE",
        "NOW(",
        "RANDOM(",
        "UUID(",
    }

    return not any(word in query.upper() for word in volatile_words)

    # Basic check: only cache SELECT queries
   
