import sqlite3
import pandas as pd

# Connect to your local SQLite database
conn = sqlite3.connect("app/assets_data.db")

# Run the SQL query (adjust table name if needed)
df = pd.read_sql_query("SELECT * FROM filled_asset_data", conn)

# Close the connection
conn.close()

# Preview the result
print(df.head())
