import sqlite3
import re
from datetime import datetime
import streamlit as st
import pandas as pd
from io import StringIO
from smatbotest import (
    extract_table_metadata,
    generate_sql_query,
    fetch_answer_from_db,
    answer_question_from_df)

def store_file_in_db(equipment_id, file_name, file_type, file_bytes):
    conn = sqlite3.connect("app/assets_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO uploads (equipment_id, file_name, file_type, upload_date, file_data) VALUES (?, ?, ?, ?, ?)",
        (equipment_id, file_name, file_type, datetime.now().isoformat(), file_bytes)
    )
    conn.commit()
    conn.close()

def handle_file_upload_and_store():
    st.subheader("📁 Upload Equipment File")
    uploaded_file = st.file_uploader(
        "Upload a PDF or image named like: EQ-3115_20_04_2025.pdf",
        type=["pdf", "jpg", "jpeg", "png"]
    )

    if uploaded_file:
        file_name = uploaded_file.name
        pattern = r"^(EQ-\d{4})_(\d{2})_(\d{2})_(\d{4})\.(pdf|jpg|jpeg|png|PDF|JPG|JPEG|PNG)$"
        match = re.match(pattern, file_name)

        if not match:
            st.error("❌ Invalid filename. Must match: EQ-XXXX_DD_MM_YYYY.ext")
            return

        equipment_id = match.group(1)
       
        file_type = uploaded_file.type
        file_bytes = uploaded_file.read()

        # Save to database
        try:
            store_file_in_db(equipment_id, file_name, file_type, file_bytes)
            st.success(f"✅ File '{file_name}' stored and linked to {equipment_id}.")
        except Exception as e:
            st.error(f"❌ Failed to save file: {str(e)}")
