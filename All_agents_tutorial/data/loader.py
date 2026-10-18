from pathlib import Path
from typing import Dict, Tuple

import duckdb
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent

DB_PATH = DATA_DIR / "analytics.duckdb"


def load_csv_data(
    data_directory: str | Path
) -> Tuple[duckdb.DuckDBPyConnection, Dict[str, pd.DataFrame]]:
    """
    Load all CSV files from a directory into DuckDB.

    Each CSV file becomes:
    1. A Pandas DataFrame
    2. A DuckDB table using the filename as the table name
    """

    data_directory = Path(data_directory)

    if not data_directory.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_directory}")

    csv_files = sorted(data_directory.glob("*.csv"))

    if not csv_files:
        raise ValueError(f"No CSV files found in data directory: {data_directory}")

    connection = duckdb.connect(str(DB_PATH))
    dataframes: Dict[str, pd.DataFrame] = {}

    for csv in csv_files:
        table = csv.stem
        data = pd.read_csv(csv)

        connection.register("temp_data", data)
        connection.execute(
            f"""
            CREATE OR REPLACE TABLE "{table}"
            AS SELECT * FROM temp_data
            """
        )

        connection.unregister("temp_data")
        dataframes[table] = data

    return connection, dataframes
