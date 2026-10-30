
from tools.inspect_data import inspect_table
from data.loader import DB_PATH
import duckdb


# these file is same as test_tool.py file script in both we are testing inspecr_data_tool .


def test_db_schema():
    
    conn = duckdb.connect(str(DB_PATH))
    try:
        table_info = inspect_table.invoke({"conn":conn})
        return table_info 
    finally:
        conn.close()


   

if __name__ == "__main__":
    schema = test_db_schema()
    print(schema)

