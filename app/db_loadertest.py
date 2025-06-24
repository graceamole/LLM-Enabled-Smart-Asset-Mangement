import pandas as pd
import sqlite3
import os

def load_data_to_sqlite(file_path="Filled_Asset_Data_csv.csv", db_name="app/assets_data.db", table_name="filled_asset_data"):
    # Load Excel or CSV
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Please use Excel or CSV.")

    print(f"Loaded {len(df)} rows from {file_path}")

    # Connect to SQLite and insert data
    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

    print(f"Data written to {db_name} (table: {table_name})")
    print(df.columns)
    print(df.head())
