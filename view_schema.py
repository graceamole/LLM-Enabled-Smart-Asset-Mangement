import sqlite3
import os

# ✅ Set the full path to your SQLite database file
db_path = "C:/Users/grace/OneDrive/Desktop/Thesis/ChatBot/app/assets_data.db"

# ✅ Optional: check if the file exists before trying to open it
if not os.path.exists(db_path):
    print("❌ Database file not found at the given path.")
else:
    try:
        # ✅ Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # ✅ SQL command to get table info: column names, types, etc.
        cursor.execute("PRAGMA table_info(filled_asset_data);")

        # ✅ Fetch all column info (returns list of tuples)
        columns = cursor.fetchall()

        # ✅ Extract and print just the column names
        print("🧩 Columns in 'filled_asset_data':")
        for col in columns:
            print(f"• {col[1]}")  # col[1] is the column name

        # ✅ Always close the connection
        conn.close()

    except sqlite3.OperationalError as e:
        print("⚠️ SQLite error:", e)
    except Exception as ex:
        print("❌ Unexpected error:", ex)
