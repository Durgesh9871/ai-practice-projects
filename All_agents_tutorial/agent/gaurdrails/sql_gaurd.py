import re


MAX_SQL_CHARACTERS = 5000

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
    "INSTALL",
    "LOAD",
}

FORBIDDEN_FUNCTIONS = {
    "READ_CSV",
    "READ_CSV_AUTO",
    "READ_PARQUET",
    "READ_JSON",
    "READ_JSON_AUTO",
    "SQLITE_SCAN",
    "POSTGRES_SCAN",
    "MYSQL_SCAN",
}


def validate_read_only_sql(sql: str) -> str:
    if not isinstance(sql, str):
        raise ValueError("SQL query must be text.")

    query = sql.strip()

    if not query:
        raise ValueError("SQL query cannot be empty.")

    if len(query) > MAX_SQL_CHARACTERS:
        raise ValueError(
            f"SQL query cannot exceed {MAX_SQL_CHARACTERS} characters."
        )

    normalized_query = query.rstrip(";").strip()

    if ";" in normalized_query:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    first_keyword_match = re.match(
        r"^\s*([A-Za-z]+)",
        normalized_query,
    )

    if not first_keyword_match:
        raise ValueError("Could not identify the SQL statement.")

    first_keyword = first_keyword_match.group(1).upper()

    if first_keyword not in {"SELECT", "WITH", "EXPLAIN"}:
        raise ValueError(
            "Only read-only SELECT, WITH, and EXPLAIN queries are allowed."
        )

    query_words = set(
        re.findall(r"\b[A-Za-z_]+\b", normalized_query.upper())
    )

    blocked_keywords = query_words.intersection(
        FORBIDDEN_KEYWORDS
    )

    if blocked_keywords:
        raise ValueError(
            "Blocked SQL keywords detected: "
            f"{', '.join(sorted(blocked_keywords))}."
        )

    upper_query = normalized_query.upper()

    for function_name in FORBIDDEN_FUNCTIONS:
        if re.search(rf"\b{function_name}\s*\(", upper_query):
            raise ValueError(
                f"Blocked SQL function detected: {function_name}."
            )

    return normalized_query