import sqlite3

# Database config
DB_PATH = "app/assets_data.db"
TABLE_NAME = "filled_asset_data"

# Connect to the SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def extract_table_metadata():
    # Fetch column names and types
    cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    schema_info = cursor.fetchall()

    # Extract just the column names
    columns = [col[1] for col in schema_info]

    # Format each column with double quotes
    quoted_cols = [f'"{col}"' for col in columns]

    # Format the SQL with multi-line layout
    indent = "  "
    joined_cols = ",\n".join([indent + col for col in quoted_cols])
    example_sql_query = f'SELECT \n{joined_cols}\nFROM {TABLE_NAME}\nWHERE [CONDITION]\nLIMIT 10;'

    return columns, example_sql_query

# Run and print
if __name__ == "__main__":
    _, sql_example = extract_table_metadata()
    print("✅ Example SQL for prompting your LLM:\n")
    print(sql_example)
