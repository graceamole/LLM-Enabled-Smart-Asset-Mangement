import os
import re
import sqlite3
from flask import Flask, request, jsonify, send_from_directory

# Initialize Flask app for chat UI
template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public'))
app = Flask(__name__, static_folder=template_folder, static_url_path='')

# -------------------------------------------
# Hard‑coded question → SQL mapping with optional "equipment"
# -------------------------------------------
QUESTION_SQL_MAP = [
    {
        "pattern": r"where is (?:equipment\s+)?(EQ-\d+)\s*located\??",
        "sql": 'SELECT "Location" FROM filled_asset_data WHERE "Equipment ID" = ?;',
        "params": lambda m: (m.group(1),)
    },
    {
        "pattern": r"who owns (?:equipment\s+)?(EQ-\d+)\??",
        "sql": 'SELECT "Asset Owner" FROM filled_asset_data WHERE "Equipment ID" = ?;',
        "params": lambda m: (m.group(1),)
    },
    {
        "pattern": r"is (?:equipment\s+)?(EQ-\d+)\s+ceased\??",
        "sql": 'SELECT "Ceased" FROM filled_asset_data WHERE "Equipment ID" = ?;',
        "params": lambda m: (m.group(1),)
    },
    {
        "pattern": r"was (?:equipment\s+)?(EQ-\d+)\s+reused\??",
        "sql": 'SELECT "Reused" FROM filled_asset_data WHERE "Equipment ID" = ?;',
        "params": lambda m: (m.group(1),)
    },
    {
        "pattern": r"what is (?:the )?engineering comment for (?:equipment\s+)?(EQ-\d+)\??",
        "sql": 'SELECT "Eng Comment" FROM filled_asset_data WHERE "Equipment ID" = ?;',
        "params": lambda m: (m.group(1),)
    },
    {
        "pattern": r"when was (?:equipment\s+)?(EQ-\d+) installed\??",
        "sql": 'SELECT "Install Date" FROM filled_asset_data WHERE "Equipment ID" = ?;',
        "params": lambda m: (m.group(1),)
    }
]


def match_question_to_sql(question: str):
    q = question.strip().lower()
    for entry in QUESTION_SQL_MAP:
        match = re.search(entry["pattern"], q)
        if match:
            return entry["sql"], entry["params"](match)
    return None, None

# -------------------------------------------
# Routes
# -------------------------------------------
@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_q = request.json.get('message', '')
    sql, params = match_question_to_sql(user_q)
    if sql is None:
        return jsonify({'reply': "Sorry, I don't understand that question."})

    try:
        conn = sqlite3.connect('app/assets_data.db')
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        conn.close()

        if row and row[0] is not None:
            return jsonify({'reply': str(row[0])})
        else:
            return jsonify({'reply': 'No data found.'})

    except Exception as e:
        return jsonify({'reply': f"Error executing query: {e}"})

