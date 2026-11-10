def normalize_sql(query: str) -> str:
    return " ".join(
        query.strip().rstrip(";").lower().split()
    )