from pathlib import Path

from data.loader import DB_PATH
from tools.inspect_data import inspect_table
import duckdb 


conn = duckdb.connect(str(DB_PATH))

inspect_table_tool = inspect_table.invoke({"conn":conn})

for table_name, table_info in inspect_table_tool["tables"].items():
    print(table_name)
    print(table_info["row_count"], "table_info")
    for column in table_info['columns']:
        print(column)


conn.close()
