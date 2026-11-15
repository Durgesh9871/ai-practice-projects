import hashlib
from agent.sql_utils import normalize_sql




def make_sql_cache_key(query: str , dbpath: str) -> str:
    """Create a cache key from function arguments."""
    normalized_query = normalize_sql(query)

    raw_query = f'{dbpath}:{normalized_query}'
    digest = hashlib.sha256(raw_query.encode('utf-8')).hexdigest()
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
   
