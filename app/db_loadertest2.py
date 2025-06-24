import pandas as pd
import sqlite3
import sys
import os

def load_data_to_sqlite(file_path, db_name="app/assets_data.db", table_name="filled_asset_data"):
    # Load Excel or CSV
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Use .csv or .xlsx")

    print(f"✅ Loaded {len(df)} rows from {file_path}")

    # Show sample data
    print(df.head())

    # Create DB directory if needed
    os.makedirs(os.path.dirname(db_name), exist_ok=True)

    # Save to SQLite
    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

    print(f"📦 Data written to {db_name} (table: {table_name})")

# -----------------------
# Script Entry Point
# -----------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️  Usage: python app/db_loader.py <path-to-file.csv>")
    else:
        file_path = sys.argv[1]
        load_data_to_sqlite(file_path)
