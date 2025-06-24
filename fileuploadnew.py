
#works to upload new documents into the db works with the v version
import sqlite3
import re
from datetime import datetime
import streamlit as st
import pandas as pd
from io import StringIO
from smatbotest_v import (
    extract_table_metadata,
    generate_sql_query,
    fetch_answer_from_db,
    answer_question_from_df)

def update_equipment_with_file(equipment_id, file_name, file_type, file_bytes):
    conn = sqlite3.connect("app/assets_data.db")
    cursor = conn.cursor()

    # Check if equipment exists
    cursor.execute('SELECT 1 FROM filled_asset_data WHERE "Equipment ID" = ?', (equipment_id,))
    exists = cursor.fetchone()
    if not exists:
        st.error(f"❌ Equipment ID '{equipment_id}' not found in database.")
        conn.close()
        return False

    # Update file fields for matching Equipment ID
    cursor.execute("""
        UPDATE filled_asset_data
        SET uploaded_file_name = ?,
            uploaded_file_type = ?,
            uploaded_file_data = ?,
            upload_date = ?
        WHERE "Equipment ID" = ?
    """, (
        file_name,
        file_type,
        file_bytes,
        datetime.now().isoformat(),
        equipment_id
    ))

    conn.commit()
    conn.close()
    return True

def handle_file_upload_and_store():
    st.subheader("📁 Upload Equipment File")

    uploaded_file = st.file_uploader(
        "Upload a PDF or Image (Name must be: EQ-xxxx_DD_MM_YYYY.pdf/jpg/png)",
        type=["pdf", "jpg", "jpeg", "png"]
    )

    if uploaded_file:
        file_name = uploaded_file.name
        pattern = r"^(EQ-\d{4})_(\d{2})_(\d{2})_(\d{4})\.(pdf|jpg|jpeg|png|PDF|JPG|JPEG|PNG)$"
        match = re.match(pattern, file_name)

        if not match:
            st.error("❌ Invalid file name. Format must be: EQ-XXXX_DD_MM_YYYY.ext")
            return

        equipment_id = match.group(1)
        file_type = uploaded_file.type
        file_bytes = uploaded_file.read()


        # Save to database
        try:
            update_equipment_with_file(equipment_id, file_name, file_type, file_bytes)
            st.success(f"✅ File '{file_name}' stored and linked to {equipment_id}.")
        except Exception as e:
            st.error(f"❌ Failed to save file: {str(e)}")
