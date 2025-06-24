import pandas as pd
import sqlite3
import os

def add_upload_columns_if_missing(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    columns = [
        ("uploaded_file_name", "TEXT"),
        ("uploaded_file_type", "TEXT"),
        ("uploaded_file_data", "BLOB"),
        ("upload_date", "TEXT")
    ]

    for column_name, column_type in columns:
        try:
            cursor.execute(f"ALTER TABLE filled_asset_data ADD COLUMN {column_name} {column_type}")
            print(f"✅ Column added: {column_name}")
        except sqlite3.OperationalError:
            print(f"ℹ️ Column already exists: {column_name}")

    conn.commit()
    conn.close()

def load_data_to_sqlite(file_path, db_name=None, table_name="filled_asset_data"):
    # Default path to app/assets_data.db
    if db_name is None:
        db_name = os.path.join(os.path.dirname(__file__), "assets_data.db")

    # Load Excel or CSV
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Use .csv or .xlsx")

    print(f"✅ Loaded {len(df)} rows from {file_path}")
    print(df.head())

    # Only make dir if needed
    dir_path = os.path.dirname(db_name)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    # Save the asset data
    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

    print(f"📦 Data written to {db_name} (table: {table_name})")

    # Ensure upload fields exist
    add_upload_columns_if_missing(db_name)

# ---------------------------
# Run script interactively
# ---------------------------
if __name__ == "__main__":
    print("📂 Enter the full path to your Excel or CSV file:")
    file_path = input("> ").strip()

    if os.path.exists(file_path):
        load_data_to_sqlite(file_path)
    else:
        print("❌ File not found. Please check the path and try again.")
