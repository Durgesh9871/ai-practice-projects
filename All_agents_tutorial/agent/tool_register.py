from tools.inspect_data import inspect_table
from tools.run_sql import run_sql_query
from langchain_core.tools import tool
import duckdb


def bind_tools(conn:duckdb.DuckDBPyConnection):

    @tool("inspect_db")
    def inspect_db()->dict:
        """
        Inspect all persistent tables in DuckDB.
        Returns table names, columns, data types, row counts,
        and a small sample of rows.
        """
        return inspect_table(conn)

    @tool("run_sql")
    def run_sql(query:str)->dict:
        """
        Execute a read-only SQL query against the DuckDB analytics database and return bounded results.
        """
        return run_sql_query(query,conn)



    return [inspect_db, run_sql]
