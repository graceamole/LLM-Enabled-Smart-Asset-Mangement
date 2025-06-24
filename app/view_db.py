import sqlite3

conn = sqlite3.connect("app/assets_data.db")
cursor = conn.cursor()

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(" Tables in DB:", cursor.fetchall())

# Show data
cursor.execute("SELECT * FROM filled_asset_data LIMIT 10;")
rows = cursor.fetchall()

print("\n Sample Data:")
for row in rows:
    print(row)

conn.close()
