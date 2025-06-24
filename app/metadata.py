import sqlite3
import pandas as pd

# Define the SQLite database and table name
DB_PATH = "app/assets_data.db"
TABLE_NAME = "filled_asset_data"

# Connect to the SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Agent 0: Extract metadata and build SQL template
def extract_table_metadata():
    # PRAGMA command to get schema info
    cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    schema_info = cursor.fetchall()

    # schema_info: [(cid, name, type, notnull, default, pk), ...]
    column_metadata = {col[1]: col[2] for col in schema_info}

    print(f"✅ Extracted metadata for table '{TABLE_NAME}':\n")
    for col, dtype in column_metadata.items():
        print(f"- {col}: {dtype}")

    # Build SQL example for prompt (with [CONDITION] placeholder)
   
    example_sql_query = f"SELECT {', '.join(column_metadata.keys())} FROM {TABLE_NAME} WHERE [CONDITION] LIMIT 10;"

    return column_metadata, example_sql_query

# Run it
if __name__ == "__main__":
    metadata, sql_template = extract_table_metadata()
    
    print("\n✅ Suggested SQL query format for LLM:")
    print(sql_template)
 