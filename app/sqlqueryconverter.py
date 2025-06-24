from metadata import extract_table_metadata
from sqlquery import extract_sql_from_response
import os
import sqlite3
import re
from groq import Groq

# Groq API key from environment
client = Groq(api_key="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")

# Set your SQLite config
DB_PATH = "app/assets_data.db"
table_name = "filled_asset_data"

def generate_sql_query(question, column_metadata, table_name="filled_asset_data"):
    prompt = f"""Generate a single SQLite SQL query to answer this question: {question}
The table is '{table_name}'. The available columns are: {', '.join(f'"{col}"' for col in column_metadata.keys())}.
Use only the relevant columns — avoid SELECT *.
Wrap all column names in double quotes.
Use LIMIT 10 if the result might contain multiple rows.
Do NOT explain — only output the SQL query.
"""

    model_name = "llama3-8b-8192"  # Choose from Groq models like llama3-8b-8192 or llama3-70b
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant who only outputs SQLite SQL queries."},
            {"role": "user", "content": prompt}
        ],
        model=model_name,
    )

    response = chat_completion.choices[0].message.content.strip()
    print(chat_completion.choices[0].message.content.strip()) 

    return extract_sql_from_response(response)

if __name__ == "__main__":
    column_metadata, example_sql_query = extract_table_metadata()
    question = "what are the top 5 equipment in our data and their owners?"

    sql_query = generate_sql_query(question, column_metadata)
    print("\n✅ Final SQL Query:\n", sql_query)
