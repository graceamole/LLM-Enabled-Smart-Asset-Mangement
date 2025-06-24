import sqlite3
import pandas as pd
import re 
from groq import Groq
from printtheanswer import fetch_answer_from_db
from sqlqueryconverter import generate_sql_query
from metadata import extract_table_metadata

client = Groq(api_key="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")
MODEL_NAME = "llama3-8b-8192"
DB_PATH = "app/assets_data.db"
table_name = "filled_asset_data"




def answer_question_from_df(question, df):
    # Prepare the DataFrame content as JSON-like structure
    df_json = df.to_json(orient='records')
    
    # Define the prompt for the LLM
    prompt = f"""Based on the following data, answer this question: {question}.
Here is the data:
{df_json}
Please provide a concise and accurate response."""
    
    model_name = 'llama-3.1-8b-instant'
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        model=model_name,
    )

    # Return the generated response from the LLM
    response = chat_completion.choices[0].message.content.strip()
    return response
column_metadata, _ = extract_table_metadata()

question = "Where is EQ-3115 located?"
sql_query =generate_sql_query(question, column_metadata, table_name)
df = fetch_answer_from_db(sql_query)
answer = answer_question_from_df(question, df)
print("\n💬 Final Answer:\n", answer)
