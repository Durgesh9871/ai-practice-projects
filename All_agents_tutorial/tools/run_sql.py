from typing import Any
from data.loader import DB_PATH
import duckdb
import re
# from langchain_core.tools import tool
from agent.guardrails.sql_guardrails import validate_read_only_sql
from agent.guardrails.pil_guardrails import redact_rows
from agent.cache.cache_keys import (
    is_cacheable_sql,
    make_sql_cache_key,
)

from agent.cache.memory_cache import sql_result_cache
from agent.config import setting

MAX_ROWS_RETURNED = 50


# FORBIDDEN_KEYWORDS = {
#     "INSERT",
#     "UPDATE",
#     "DELETE",
#     "DROP",
#     "ALTER",
#     "TRUNCATE",
#     "CREATE",
#     "ATTACH",
#     "DETACH",
#     "COPY",
# }


# def validate_read_only_sql(sql:str):
#     """
#     Basic validation to prevent accidental data modification by LLM.
#     """
#     query = sql.strip()

#     if not query:
#         raise ValueError("SQL query cannot be empty.")

#     normalize_query = query.rstrip(";").strip()

#     if ";" in normalize_query:
#         raise ValueError("Multiple SQL statements detected. Only single SELECT statements are allowed.")

#     first_keyword_match = re.match(r"^\s*([A-Za-z]+)",normalize_query)

#     if not first_keyword_match:
#         raise ValueError("Not able to indentify SQL query.")

#     first_keyword = first_keyword_match.group(1).upper()
    

#     if first_keyword not in ["SELECT","WITH","EXPLAIN"]:
#         raise ValueError(f"Please use only read-only SQL. Avoid: {first_keyword}.")

#     query_words = set(
#         re.findall(r"\b[A-Za-z]+\b", normalize_query.upper())
#     )  

#     blocked_keywords = query_words.intersection(FORBIDDEN_KEYWORDS)     

#     if blocked_keywords:
#         raise ValueError(f"Blocked SQL keywords detected: {', '.join(blocked_keywords)}.")
    


def run_sql_query(query:str,conn:duckdb.DuckDBPyConnection)->dict[str,Any]:

    try:
        validate_read_only_sql(query)
        
        if is_cacheable_sql(query):
            cache_key = make_sql_cache_key(query , dbpath=str(DB_PATH.resolve()),)
            cached_result = sql_result_cache.get(cache_key)
            if cached_result is not None:
                return {
                    **cached_result,
                    "cache_hit": True,
                }

        cursor = conn.execute(query)
        columns = [
            column[0]
            for column in cursor.description
        ]

        raw_rows = cursor.fetchmany(MAX_ROWS_RETURNED + 1)
        truncated = len(raw_rows) > MAX_ROWS_RETURNED
        limited_rows = raw_rows[:MAX_ROWS_RETURNED]
        
        
        rows = []
        for row in limited_rows:
            row_dict = dict(zip(columns, row))
            rows.append(row_dict)

        safe_rows = redact_rows(rows)
        # total_rows = len(data_frame)
        # limited_dataframe = data_frame.head(MAX_ROWS_RETURNED) 

        result = {
            "success": True,
            "columns": columns,
            "rows": safe_rows,
            "row_count": None if truncated else len(safe_rows),
            "returned_rows": len(safe_rows),
            "truncated": truncated,
            "cache_hit": False,
        }
        
        if is_cacheable_sql(query):
            sql_result_cache.set(cache_key, result, setting.sql_cache_ttl_seconds)
        
        return result


    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }   