##this workks
import os
import sqlite3
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import faiss
import time

app = Flask(__name__, static_folder='../public', static_url_path='')

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

# -------------------------------------------
# Step 1: Load SQLite Data + Generate Embeddings
# -------------------------------------------
print("📦 Loading SQLite data...")
conn = sqlite3.connect("app/assets_data.db")
df = pd.read_sql_query("SELECT * FROM filled_asset_data", conn)
conn.close()

print("✅ Loaded", len(df), "rows")

# ✅ Normalize column names
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# ✅ Fill NaNs and build embedding text per row dynamically
texts = df.fillna("").apply(lambda row: " | ".join([f"{col}: {row[col]}" for col in df.columns]), axis=1)

print("🔍 Generating embeddings...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embedder.encode(texts.tolist(), convert_to_numpy=True)

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)
id_to_text = {i: t for i, t in enumerate(texts)}

# -------------------------------------------
# Step 2: Load Local LLM (phi-1_5)
# -------------------------------------------
print("🤖 Loading local LLM (phi-1_5)...")
tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-1_5")
model = AutoModelForCausalLM.from_pretrained("microsoft/phi-1_5")
llm = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256)

# -------------------------------------------
# Step 3: Define RAG Functions
# -------------------------------------------
def get_similar_chunks(question, top_k=3):
    q_embedding = embedder.encode([question])[0]
    D, I = index.search(np.array([q_embedding]), top_k)
    return [id_to_text[i] for i in I[0]]

def ask_llm(question, context_chunks):
    context = "\n".join(context_chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    print("🧠 Prompt ready. Passing to LLM...")
    result = llm(prompt, return_full_text=False)[0]["generated_text"]
    return result.strip()

# -------------------------------------------
# Step 4: Flask Chat Endpoint
# -------------------------------------------
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    try:
        print("🔍 Question received:", user_input)

        print("📚 Retrieving relevant data chunks...")
        start = time.time()
        chunks = get_similar_chunks(user_input)
        print(f"📊 Retrieved {len(chunks)} chunks in {round((time.time()-start)*1000)}ms")
        print("⏳ Generating answer...")

        # Simulate percentage loading
        for percent in range(0, 101, 20):
            print(f"⏳ LLM processing... {percent}%")
            time.sleep(0.1)

        answer = ask_llm(user_input, chunks)

        print("✅ Final Answer:", answer)
        return jsonify({'reply': answer})

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({'reply': "❌ Something went wrong. Try again."})
