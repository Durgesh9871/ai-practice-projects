from pathlib import Path

from data.loader import DB_PATH, load_csv_data


DATA_DIRECTORY = Path("data/ecommerce_demo")


connection, dataframes = load_csv_data(DATA_DIRECTORY)

print("Database path:")
print(DB_PATH)

print("\nLoaded DataFrames:")
print(list(dataframes.keys()))

print("\nDuckDB tables:")
print(connection.execute("SHOW TABLES").fetchall())

print("\nRow counts:")
for table_name in dataframes:
    count = connection.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]

    print(f"{table_name}: {count}")

print("\nOrders sample:")
print(connection.execute("SELECT * FROM orders LIMIT 5").fetchdf())

connection.close()
