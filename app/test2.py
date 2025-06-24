import sqlite3

conn = sqlite3.connect("assets_data.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Available tables:", tables)
conn.close()