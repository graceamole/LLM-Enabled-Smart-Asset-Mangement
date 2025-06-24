import sqlite3
import pandas as pd
import re
import os
from groq import Groq

# -----------------------------
# Config
# -----------------------------
DB_PATH = "app/assets_data.db"
TABLE_NAME = "filled_asset_data"
client = Groq(api_key="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")
MODEL_NAME = "llama3-8b-8192"

# -----------------------------
# Agent 0: Extract Table Metadata
# -----------------------------
def extract_table_metadata():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    schema_info = cursor.fetchall()
    conn.close()

    column_metadata = {col[1]: col[2] for col in schema_info}
    
    print(f"✅ Extracted metadata from '{TABLE_NAME}':")
    for col, dtype in column_metadata.items():
        print(f"- {col}: {dtype}")

    #example_sql_query = f'SELECT {", ".join([f\'"{col}"\' for col in column_metadata])} FROM {TABLE_NAME} WHERE [CONDITION] LIMIT 10;'
    example_sql_query = f"SELECT {', '.join(column_metadata.keys())} FROM {TABLE_NAME} WHERE [CONDITION] LIMIT 10;"
    return column_metadata, example_sql_query

# -----------------------------
# Utility: Extract first SQL query from LLM output
# -----------------------------
# def extract_sql_from_response(response):
#     queries = re.findall(r"SELECT.*?;", response, re.IGNORECASE | re.DOTALL)
 #    if queries:
 #        return queries[0].strip().rstrip(';')
 #    else:
 #        raise ValueError("No valid SQL query found.")
   

# -----------------------------
# Agent 1: Convert NL → SQL via LLM
# -----------------------------
def generate_sql_query(question,  example_sql_query,column_metadata, TABLE_NAME):
    prompt = f"""Generate a single SQLite SQL query for this question: {question}. The Table is
'{TABLE_NAME}'.The available columns are  {', '.join(f'"{col}"' for col in column_metadata.keys())}.
Use only the relevant columns - Avoid SELECT *.
Wrap all column names in double quotes.
Use LIMIT 10 if the result might contain multiple rows
Do NOT explain — only output the SQL query.
Follow this example as guidance:


Example SQL Query:
{example_sql_query}

Respond ONLY with valid SQL — no explanations.
"""
    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that only responds with valid SQLite SQL."},
            {"role": "user", "content": prompt}
        ],
    )

    response = chat_completion.choices[0].message.content.strip()
    sql_query = extract_sql_from_response(response)
    print("\LLM Raw Output:\n", response)
    return sql_query


# -----------------------------
# Agent 2: Execute SQL → DataFrame
# -----------------------------
def fetch_answer_from_db(sql_query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql_query)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=columns)
    return df

# -----------------------------
# Agent 3: Convert DataFrame → Final Answer
# -----------------------------
def answer_question_from_df(question, df):
    if df.empty:
        return "No results found."

    df_json = df.to_json(orient='records')
    prompt = f"""Based on the following data, answer this question: {question}.
Here is the data:
{df_json}
Provide a concise and accurate response.
"""

    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
    )
    
    response = chat_completion.choices[0].message.content.strip()
    return response
# -----------------------------
# 🎯 Main Handler: One-liner to Rule Them All
# -----------------------------
def handle_question(question):
    print(f"\n🔎 Question: {question}\n")
    
    # Step 0: Extract metadata
    column_metadata, example_sql_query = extract_table_metadata()

    # Step 1: Generate SQL
    sql_query = generate_sql_query(question, column_metadata, example_sql_query)
    print(f"\n Generated SQL:\n{sql_query}\n")

    # Step 2: Run the SQL
    df = fetch_answer_from_db(sql_query)
    print("Fetched Data in DataFrame:")
    print(df)
    print("Query Result:\n", df if not df.empty else "No data found.")

    # Step 3: LLM-formatted answer
    answer = answer_question_from_df(question, df)
    print(f" Final Answer:\n{answer}")

# -----------------------------
# 🧪 Example
# -----------------------------
if __name__ == "__main__":
    question = "list 5 equipments and their location?"
    handle_question(question)