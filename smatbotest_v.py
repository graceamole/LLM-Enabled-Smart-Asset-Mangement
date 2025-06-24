# smartbo test.py (Updated with underscore column names for documents)
import sqlite3
import pandas as pd
import re
import os
from groq import Groq
import streamlit as st
import time


# -----------------------------
# Config
# -----------------------------
DB_PATH = "app/assets_data.db"
TABLE_NAME = "filled_asset_data"
client = Groq(api_key="")
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

    # Store column names exactly as they are in the database (with spaces or underscores)
    column_metadata = {col[1]: col[2] for col in schema_info}
    
    # Example SQL query now correctly quotes column names with spaces or handles underscores
    example_sql_query = f"SELECT {', '.join([f'\"{col}\"' if ' ' in col or '-' in col else col for col in column_metadata.keys()])} FROM \"{TABLE_NAME}\" WHERE [CONDITION] LIMIT 10;"
    return column_metadata, example_sql_query


# -----------------------------
# Agent 1: Convert NL → SQL via LLM
# -----------------------------
def generate_sql_query(question, example_sql_query, column_metadata, table_name):
    # Prepare schema string for the prompt, quoting columns with spaces or handling underscores
    schema_str = "\n".join([f"    \"{col}\": {dtype}" if ' ' in col or '-' in col else f"    {col}: {dtype}" for col, dtype in column_metadata.items()])
    
    prompt = f"""
    You are a helpful and precise AI assistant that converts natural language questions into **complete and executable SQLite SQL queries**.

    You are given the following database schema for the table '{table_name}':

    ```
    {schema_str}
    ```

    **Instructions for generating SQL:**
    1.  Always generate a complete SQL query, including the `SELECT` and `FROM \"{table_name}\"` clauses.
    2.  Strictly use the column names exactly as they appear in the `CREATE TABLE` statement. **Enclose column names containing spaces or hyphens in double quotes (e.g., "Equipment ID", "Asset-Name"). For names with underscores (e.g., uploaded_file_name), quotes are typically not needed unless they are keywords, but it's safer to always quote if there's any ambiguity.**
    3.  **Crucially, select ONLY the specific columns that directly answer the user's question.** Do NOT use `SELECT *` unless the user explicitly asks for "all columns" or "all details".
    4.  Do NOT add `GROUP BY`, `ORDER BY`, or `LIMIT` clauses unless explicitly requested by the user in their question.
    5.  For date-related questions (e.g., involving years), use SQLite's `STRFTIME('%Y', "column name")` for year extraction if the column is in a standard date format. If the date format is consistently `DD/MM/YYYY`, you may use `SUBSTR("column name", 7, 4)` to extract the year. Remember to quote column names with spaces or hyphens if applicable.

    Respond ONLY with the valid SQL query. Do NOT include any other text, explanations, or conversational elements. Enclose the SQL query in a markdown code block (```sql ... ```).

    Examples of desired SQL:
    - User Question: "Where is equipment EQ-3115 located?"
      SQL: `SELECT "Location" FROM \"{table_name}\" WHERE "Equipment ID" = 'EQ-3115';`
    - User Question: "What is the Asset Name for part P-12345?"
      SQL: `SELECT "Asset Name" FROM \"{table_name}\" WHERE "Part ID" = 'P-12345';`
    - User Question: "Show me all details for EQ-3115"
      SQL: `SELECT * FROM \"{table_name}\" WHERE "Equipment ID" = 'EQ-3115';`

    User Question: {question}
    """
    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.0, # Set temperature to 0 for deterministic output, crucial for evaluation
        max_tokens=500, # Max tokens for the SQL query
    )

    response = chat_completion.choices[0].message.content.strip()
    return extract_sql_from_response(response)


# -----------------------------
# Utility: Extract first SQL query from LLM output
# -----------------------------
def extract_sql_from_response(response):
    # This regex looks for a markdown code block first
    markdown_match = re.search(r"```sql\n(.*?)```", response, re.IGNORECASE | re.DOTALL)
    if markdown_match:
        return markdown_match.group(1).strip().rstrip(';')
    
    # Fallback: if no markdown block, try to find the first SELECT statement
    queries = re.findall(r"SELECT.*?;", response, re.IGNORECASE | re.DOTALL)
    if queries:
        return queries[0].strip().rstrip(';')
    else:
        # If still no SQL, raise an error
        raise ValueError(f"No valid SQL query found in response: {response}")


# -----------------------------
# Agent 2: Execute SQL → DataFrame
# -----------------------------
def fetch_answer_from_db(sql_query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        df = pd.DataFrame(cursor.fetchall(), columns=columns)
        return df
    except sqlite3.Error as e:
        st.error(f"SQL Execution Error: {e}\nQuery: {sql_query}")
        return pd.DataFrame() # Return empty DataFrame on error
    finally:
        conn.close()

# -----------------------------
# New Agent: Generate SQL for Document Retrieval (BLOB Data)
# -----------------------------
def generate_document_sql_query(question, column_metadata, table_name):
    """
    Generates a SQL query to retrieve document BLOB data and its metadata
    (uploaded_file_name, uploaded_file_type, uploaded_file_data).
    """
    # CORRECTED: Using underscore column names as confirmed by user
    document_data_columns = [
        "uploaded_file_name",
        "uploaded_file_type",
        "uploaded_file_data" # This is your BLOB column
    ]

    # Validate that these columns actually exist in the schema
    # The keys in column_metadata will match the exact names from PRAGMA table_info
    if not all(col in column_metadata for col in document_data_columns):
        missing_cols = [col for col in document_data_columns if col not in column_metadata]
        st.error(f"Error: Missing expected document BLOB columns in database schema: {', '.join(missing_cols)}. Please ensure your '{table_name}' table contains these exact columns and they are populated.")
        # Return a simple, non-crashing query as a fallback
        fallback_col = list(column_metadata.keys())[0] if column_metadata else "Equipment ID" 
        if "Equipment ID" in column_metadata: 
            fallback_col = "Equipment ID"
        return f"SELECT \"{fallback_col}\" FROM \"{table_name}\" LIMIT 1;"


    # Ensure relevant filtering columns are available (using exact names from schema)
    available_filter_cols = [col for col in ["Equipment ID", "Asset Name", "Serial No", "Part ID"] if col in column_metadata]
    filter_clause_hint = ""
    if available_filter_cols:
        filter_clause_hint = f"You can filter by columns like {', '.join([f'\"{c}\"' if ' ' in c or '-' in c else c for c in available_filter_cols])}."

    # Prepare schema string for the prompt, quoting columns with spaces or handling underscores
    schema_str = "\n".join([f"    \"{col}\": {dtype}" if ' ' in col or '-' in col else f"    {col}: {dtype}" for col, dtype in column_metadata.items()])

    prompt = f"""
    You are a helpful and precise AI assistant that converts natural language questions into **complete and executable SQLite SQL queries** to retrieve **document BLOB data and its metadata** for specific assets.

    You are given the following database schema for the table '{table_name}':

    ```
    {schema_str}
    ```

    **Instructions for generating SQL for documents:**
    1.  The user is asking for images, PDFs, or manuals related to an equipment.
    2.  **Crucially, your SELECT query MUST ALWAYS retrieve the following columns: `"uploaded_file_name"`, `"uploaded_file_type"`, and `"uploaded_file_data"`.** These three columns are absolutely essential for document retrieval and display. You may also include identifying columns like `"Equipment ID"` and `"Asset Name"` if the question implies filtering by them, but the three document-related columns are mandatory.
    3.  Always include the `FROM \"{table_name}\"` clause.
    4.  Strictly use the column names exactly as they appear in the `CREATE TABLE` statement. **Enclose column names containing spaces or hyphens in double quotes (e.g., "Equipment ID"). For names with underscores (e.g., uploaded_file_name), quotes are typically not needed unless they are keywords, but it's safer to always quote if there's any ambiguity.**
    5.  Use a `WHERE` clause to filter by specific equipment details mentioned in the question (e.g., `"Equipment ID"`, `"Asset Name"`, `"Serial No"`, `"Part ID"`). {filter_clause_hint}
    6.  Ensure the `"uploaded_file_data"` column is NOT NULL in the WHERE clause, to only retrieve records with actual files.
    7.  Do NOT add `GROUP BY`, `ORDER BY`, or `LIMIT` clauses unless explicitly requested.
    8.  Respond ONLY with the valid SQL query. Do NOT include any other text, explanations, or conversational elements. Enclose the SQL query in a markdown code block (```sql ... ```).

    User Question: {question}
    """
    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=500,
    )

    response = chat_completion.choices[0].message.content.strip()
    return extract_sql_from_response(response)


# -----------------------------
# New Agent: Fetch Document BLOBs from DB
# -----------------------------
def fetch_document_blobs_from_db(sql_query):
    """
    Executes a SQL query to fetch document BLOB data and returns them as a DataFrame.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        # Use pd.read_sql_query directly, it's robust with BLOBs
        df = pd.read_sql_query(sql_query, conn)
        return df
    except sqlite3.Error as e:
        st.error(f"SQL Execution Error during document BLOB retrieval: {e}\nQuery: {sql_query}")
        return pd.DataFrame() # Return empty DataFrame on error
    finally:
        conn.close()

# -----------------------------
# Agent 3: Convert DataFrame → Final Answer
# -----------------------------
def answer_question_from_df(question, df):
    if df.empty:
        return "No results found."

    # Robustly handle non-UTF-8 characters in DataFrame before converting to JSON
    # Iterate through string columns and attempt aggressive ASCII conversion
    for col in df.select_dtypes(include=['object']).columns:
        if not df[col].empty and df[col].notna().any():
            # Apply encoding to ASCII, ignoring errors, then decode back to UTF-8
            # This is a more aggressive cleaning, replacing problematic characters
            # with nothing if they cannot be represented in ASCII.
            df[col] = df[col].apply(lambda x: str(x).encode('ascii', 'ignore').decode('utf-8') if isinstance(x, str) else x)

    df_json = df.to_json(orient='records')
    prompt = f"""Based on the following data, answer this question: {question}.
Here is the data:
{df_json}
Provide a concise and accurate response.
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        model=MODEL_NAME,
    )
    
    return chat_completion.choices[0].message.content.strip()

# -----------------------------
# Utility: Determine display type from MIME type
# -----------------------------
def _get_display_type(file_type):
    """Determines if a file_type (MIME type) is an image or PDF for display purposes."""
    if isinstance(file_type, str):
        file_type_lower = file_type.lower()
        if 'image/' in file_type_lower:
            return 'image'
        elif 'application/pdf' in file_type_lower:
            return 'pdf'
    return 'other' # For types not explicitly handled for direct display

# -----------------------------
# Run with Retries (Updated for clarity and Streamlit display)
# -----------------------------
def run_with_retries(question, retries=3):
    success = False
    attempt = 0
    result_df = None
    answer = None

    while attempt < retries and not success:
        try:
            attempt += 1
            column_metadata, example_sql_query = extract_table_metadata() # Get both
            sql_query = generate_sql_query(question, example_sql_query, column_metadata, TABLE_NAME)
            
            # st.subheader(f"Generated SQL Query (Attempt {attempt})") # This will be handled by chatbit_ui.py
            # st.code(sql_query) # This will be handled by chatbit_ui.py

            result_df = fetch_answer_from_db(sql_query)
            answer = answer_question_from_df(question, result_df)
            
            success = True
        except Exception as e:
            st.warning(f"Attempt {attempt} failed with error: {e}")
            time.sleep(1)
    
    if success:
        return result_df, answer
    else:
        st.error("Failed to process the request after multiple attempts.")
        return None, None
