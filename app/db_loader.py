import pandas as pd
import sqlite3
import os
import  tkinter
from tkinter  import Tk, filedialog


def load_data_to_sqlite(file_path, db_name=None, table_name="filled_asset_data"):
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

    #os.makedirs(os.path.dirname(db_name), exist_ok=True)
    dir_path = os.path.dirname(db_name)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

    print(f"📦 Data written to {db_name} (table: {table_name})")

if __name__ == "__main__":
    # Open file picker window
   print("📂 Enter the full path to your Excel or CSV file:")
   file_path = input("> ")

if os.path.exists(file_path):
        load_data_to_sqlite(file_path)
else:
    print(" File not found. Please check the path and try again.")