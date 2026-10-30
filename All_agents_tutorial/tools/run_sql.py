from typing import Any
from data.loader import DB_PATH
import duckdb
import re
# from langchain_core.tools import tool


MAX_ROWS_RETURNED = 50


FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "ATTACH",
    "DETACH",
    "COPY",
}


def validate_read_only_sql(sql:str):
    """
    Basic validation to prevent accidental data modification by LLM.
    """
    query = sql.strip()

    if not query:
        raise ValueError("SQL query cannot be empty.")

    normalize_query = query.rstrip(";").strip()

    if ";" in normalize_query:
        raise ValueError("Multiple SQL statements detected. Only single SELECT statements are allowed.")

    first_keyword_match = re.match(r"^\s*([A-Za-z]+)",normalize_query)

    if not first_keyword_match:
        raise ValueError("Not able to indentify SQL query.")

    first_keyword = first_keyword_match.group(1).upper()
    

    if first_keyword not in ["SELECT","WITH","EXPLAIN"]:
        raise ValueError(f"Please use only read-only SQL. Avoid: {first_keyword}.")

    query_words = set(
        re.findall(r"\b[A-Za-z]+\b", normalize_query.upper())
    )  

    blocked_keywords = query_words.intersection(FORBIDDEN_KEYWORDS)     

    if blocked_keywords:
        raise ValueError(f"Blocked SQL keywords detected: {', '.join(blocked_keywords)}.")
    


# @tool("run_sql_query")
def run_sql_query(query:str,conn:duckdb.DuckDBPyConnection)->dict[str,Any]:

    try:
        validate_read_only_sql(query)

        data_frame = conn.execute(query).fetchdf()

        total_rows = len(data_frame)
        limited_dataframe = data_frame.head(MAX_ROWS_RETURNED)   


        return {
            "success": True,
            "columns": list(limited_dataframe.columns),
            "rows": limited_dataframe.to_dict(orient="records"),
            "row_count": total_rows,
            "returned_rows": len(limited_dataframe),
            "truncated": total_rows > MAX_ROWS_RETURNED,
        }


    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }   