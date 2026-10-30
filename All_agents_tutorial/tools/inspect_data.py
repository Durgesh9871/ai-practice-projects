from typing import Any 
import duckdb
# from langchain_core.tools import tool


# @tool("Inspect Table")
def inspect_table(conn: duckdb.DuckDBPyConnection) -> str:
    try:
        table =[t[0] for t in conn.execute("SHOW TABLES").fetchall()]
        if not table:
            return "No tables found in the database."

        result:dict[str,Any]={
            "tables":{}
        }
    
        for table in table:
            columns = conn.execute(f"DESCRIBE {table}").fetchdf()
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            sample_rows = conn.execute(f"SELECT * FROM {table} LIMIT 3").fetchdf().to_dict(orient="records")

            result["tables"][table]={
                "columns":[
                    {"name":col["column_name"],"type":col["column_type"]}
                    for col in columns.to_dict(orient="records")
                ],
                "row_count":row_count,
                "sample_rows":sample_rows
            }


        return result   
    
    except Exception as e:
        return f"Error inspecting database: {str(e)}" 

    
   
    
