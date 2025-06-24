from groq import Groq
import sqlite3
import pandas as pd
from metadata import extract_table_metadata
from sqlqueryconverter import generate_sql_query

# Config
DB_PATH = "app/assets_data.db"
table_name = "filled_asset_data"


# Connect to SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Fetch result from DB
def fetch_answer_from_db(sql_query):
    cursor.execute(sql_query)
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchall()
    df = pd.DataFrame(result, columns=columns)
    return df

# Sample question
question = "What are the top 10 equipment models?"
column_metadata, _ = extract_table_metadata()

# Generate SQL from LLM
sql_query = generate_sql_query(question, column_metadata, table_name)

# Run query
df = fetch_answer_from_db(sql_query)

# Display result
print(df if not df.empty else "No results found.")
