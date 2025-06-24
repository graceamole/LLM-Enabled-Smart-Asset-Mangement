# chatbit_ui.py (Updated for underscore column names for documents)
import streamlit as st
import pandas as pd
from io import StringIO
import base64 

# Import all necessary functions from your smartbo test.py
# Make sure your smartbo test.py file is named 'smatbotest.py'
# or adjust this import statement accordingly.
from smatbotest_v import (
    extract_table_metadata,
    generate_sql_query,
    fetch_answer_from_db,
    answer_question_from_df,
    # New imports for document feature:
    generate_document_sql_query,
    fetch_document_blobs_from_db,
    _get_display_type 
)
# Assuming fileuploadnew is a separate module for handling uploads,
# though it's not directly used in the query/document retrieval flow.
from fileuploadnew import handle_file_upload_and_store 


st.set_page_config(layout="centered")
st.title("Ask Your Equipment Database")

# Create tabs for different functionalities
tab1, tab2 = st.tabs(["Text-to-SQL Query", "Document Retrieval"])

# ---------------------------------
# Tab 1: Text-to-SQL Query
# ---------------------------------
with tab1:
    st.header("Query Your Database with Natural Language")
    question_sql = st.text_input("Enter your question:", placeholder="e.g. Where is EQ-3115 located?", key="sql_query_input")

    if st.button("Submit Query", key="submit_sql_query"):
        with st.spinner("Generating SQL and fetching results..."):
            try:
                # Agent 0: Get schema
                column_metadata, example_sql_query = extract_table_metadata()

                # Agent 1: Generate SQL query
                sql_query = generate_sql_query(question_sql, example_sql_query, column_metadata, "filled_asset_data")
                
                # Hide SQL query in an expander
                with st.expander("Show Generated SQL Query"):
                    st.code(sql_query, language="sql")

                # Agent 2: Execute SQL query
                df = fetch_answer_from_db(sql_query)

                # Agent 3: Answer from LLM
                answer = answer_question_from_df(question_sql, df)

                st.subheader("LLM Answer")
                st.write(answer)

                st.subheader("Retrieved Data")
                if df is not None and not df.empty:
                    st.dataframe(df)
                else:
                    st.info("No matching data found.")

            except Exception as e:
                st.error(f"Error occurred during SQL query: {str(e)}")

# ---------------------------------
# Tab 2: Document Retrieval (New Feature)
# ---------------------------------
with tab2:
    st.header("Retrieve Documents (Images, PDFs, Manuals)")
    document_question = st.text_input(
        "Ask for a document (e.g., 'Show me the image for EQ-3115' or 'Get the manual for Asset ABC'):",
        key="doc_query_input"
    )

    if st.button("Retrieve Document", key="submit_doc_query"):
        with st.spinner("Searching for documents..."):
            try:
                # Agent 0: Get schema (needed for LLM context)
                column_metadata, _ = extract_table_metadata()

                # Generate SQL query for documents
                doc_sql_query = generate_document_sql_query(document_question, column_metadata, "filled_asset_data")
                
                # Hide SQL query in an expander
                with st.expander("Show Generated Document SQL Query"):
                    st.code(doc_sql_query, language="sql")

                # Fetch document BLOBs
                docs_df = fetch_document_blobs_from_db(doc_sql_query)

                st.subheader("Retrieved Documents:")
                if docs_df is not None and not docs_df.empty:
                    # Validate that the required columns are present in the DataFrame
                    required_doc_cols = ["uploaded_file_name", "uploaded_file_type", "uploaded_file_data"]
                    
                    # Ensure this block is correctly indented
                    if not all(col in docs_df.columns for col in required_doc_cols):
                       missing_cols = [col for col in required_doc_cols if col not in docs_df.columns]
                       st.error(f"Error: The generated SQL query did not return all required document columns. Missing: {', '.join(missing_cols)}. Please ensure the generated SQL includes 'uploaded_file_name', 'uploaded_file_type', and 'uploaded_file_data' in its SELECT clause.")
                       st.dataframe(docs_df) 
                     # This return is now correctly inside the 'if' block
                        
                    # Filter out rows where "uploaded_file_data" is None or empty
                    docs_df_clean = docs_df[docs_df['uploaded_file_data'].notna() & (docs_df['uploaded_file_data'] != b'')]
                    
                    if docs_df_clean.empty:
                        st.info("No documents found for your query or documents have no data.")
                    else:
                        for index, row in docs_df_clean.iterrows():
                            # Use .get() for robust access, providing a default if column is missing (though it shouldn't be after schema check)
                            file_name = row.get('uploaded_file_name', f'Unknown Document {index+1}')
                            file_type = row.get('uploaded_file_type', 'application/octet-stream')
                            file_data_blob = row.get('uploaded_file_data')
                            equipment_id = row.get('Equipment ID', 'N/A') # Get Equipment ID if available in select

                            if file_data_blob:
                                display_type = _get_display_type(file_type)
                                
                                st.write(f"--- Document for Equipment ID: **{equipment_id}** ---")
                                st.write(f"**File Name:** {file_name}")
                                st.write(f"**File Type:** {file_type}")

                                if display_type == 'image':
                                    try:
                                        st.image(file_data_blob, caption=file_name, use_column_width=True)
                                    except Exception as img_e:
                                        st.warning(f"Could not display image {file_name}: {img_e}")
                                    
                                elif display_type == 'pdf':
                                    st.info("This is a PDF document.")
                                    # Optional: For small PDFs, you could try embedding via base64, but it can be slow/resource intensive for large files.
                                    # For simplicity and reliability, primarily offer download.
                                    
                                else:
                                    st.info("This is a document of an unknown type for direct display. Please download it.")

                                # Provide a download button for all retrieved files
                                st.download_button(
                                    label=f"Download {file_name}",
                                    data=file_data_blob,
                                    file_name=file_name,
                                    mime=file_type,
                                    key=f"download_doc_{index}"
                                )
                                st.markdown("---") # Separator between documents

                else:
                    st.info("No documents found matching your criteria.")

            except Exception as e:
                st.error(f"Error occurred during document retrieval: {str(e)}")

    # The file upload component is now exclusively inside the "Document Retrieval" tab
    handle_file_upload_and_store()
