#this works with stream flask
import streamlit as st
import pandas as pd
from io import StringIO
from smatbotest import (
    extract_table_metadata,
    generate_sql_query,
    fetch_answer_from_db,
    answer_question_from_df)
from fileuploadnew import handle_file_upload_and_store
  

st.set_page_config(layout="centered")
st.title("Ask Your Equipment Database")

# ---------------------------------
# Ask Question (Row 1)
# ---------------------------------
question = st.text_input("Enter your question:", placeholder="e.g. Where is EQ-3115 located?")

if st.button("Submit"):
    with st.spinner("Running... Please wait."):
        try:
            # Agent 0: Get schema
            column_metadata, example_sql_query = extract_table_metadata()

            # Agent 1: Generate SQL query
            sql_query = generate_sql_query(question, example_sql_query, column_metadata, "filled_asset_data")

            # Agent 2: Execute SQL query
            df = fetch_answer_from_db(sql_query)

            # Agent 3: Answer from LLM
            answer = answer_question_from_df(question, df)

            # ---------------------------------
            # Row 2: Display Answer
            # ---------------------------------
            st.subheader("LLM Answer")
            st.write(answer)

            # ---------------------------------
            # Row 3: Display DataFrame
            # ---------------------------------
            st.subheader("Retrieved Data")
            if df is not None and not df.empty:
                st.dataframe(df)
            else:
                st.info("No matching data found.")

        except Exception as e:
            st.error(f"Error occurred: {str(e)}")

handle_file_upload_and_store()