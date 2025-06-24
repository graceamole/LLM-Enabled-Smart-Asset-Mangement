#!/usr/bin/env python
"""
evaluate_llm.py
--------------------------------------------
One-file benchmark that

1. Turns natural-language questions about an SQLite table into SQL
2. Executes the SQL, turns the rows back into a final answer
3. Measures • accuracy  • latency  • peak RAM  • energy / CO₂
--------------------------------------------
"""

import os, re, sqlite3, time, tracemalloc, random, types, sys, pandas as pd
import psutil
from typing import Dict
from codecarbon import EmissionsTracker
from deepeval.metrics import ExactMatchMetric
from deepeval.dataset import EvaluationDataset
from deepeval import evaluate
from groq import Groq

try:                                     # older Deepeval
    from deepeval.metrics import ExactMatchMetric
    from deepeval.run    import run_evaluations as evaluate
except ImportError:                      # 0.25+
    from deepeval.metrics.text import ExactMatchMetric
    from deepeval import evaluate
    
exact = ExactMatchMetric(strict=False)

# ────────────────────────────────────────────────
# Config — change here only
# ────────────────────────────────────────────────
DB_PATH     = "app/assets_data.db"
TABLE_NAME  = "filled_asset_data"
CSV_GOLDSET = "Filled_Asset_Data_csv.csv"
MODEL_NAME  = "llama3-8b-8192"
SAMPLE_SIZE = 10                       # ▲ raise to 100/1000 for bigger tests
GROQ_KEY    = "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"

# fall back to a stub Streamlit so imports don’t crash
stub = types.ModuleType("streamlit")
stub.subheader = stub.code = stub.warning = stub.error = lambda *a, **k: None
sys.modules["streamlit"] = stub

# ────────────────────────────────────────────────
# Core pipeline (metadata → SQL → DataFrame → answer)
# ────────────────────────────────────────────────
client = Groq(api_key=GROQ_KEY)

def extract_table_metadata() -> tuple[Dict[str, str], str]:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(f"PRAGMA table_info({TABLE_NAME})")
    info = cur.fetchall()
    conn.close()
    cols = {col[1]: col[2] for col in info}
    example = f"SELECT {', '.join(cols.keys())} FROM {TABLE_NAME} WHERE [CONDITION] LIMIT 10;"
    return cols, example

def generate_sql(question: str, cols: Dict[str, str], example_sql: str) -> str:
    prompt = f"""Generate a single SQLite SQL query for: {question}
Table: "{TABLE_NAME}"  Columns: {', '.join(f'"{c}"' for c in cols)}
Avoid SELECT *, wrap names in double quotes, LIMIT 10 if >1 row.
Reply ONLY with SQL (no prose).

Example:
{example_sql}
"""
    chat = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role":"system","content":"You are a helpful assistant that only outputs SQLite."},
            {"role":"user",  "content":prompt}
        ],
    )
    raw = chat.choices[0].message.content.strip()
    match = re.findall(r"SELECT.*?;", raw, re.I | re.S)
    if not match:
        raise ValueError("No SQL detected")
    return match[0].rstrip(';')

def fetch_df(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(sql, conn)
    conn.close()
    return df

def answer_from_df(question: str, df: pd.DataFrame) -> str:
    if df.empty:
        return "No results found."
    chat = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role":"system","content":"You are a helpful assistant."},
            {"role":"user",
             "content":f"Answer: {question}\nData:\n{df.to_json(orient='records')}"}
        ],
    )
    return chat.choices[0].message.content.strip()

def ask(question: str, retries: int = 3) -> str:
    cols, ex = extract_table_metadata()
    last = None
    for _ in range(retries):
        try:
            sql = generate_sql(question, cols, ex)
            df  = fetch_df(sql)
            return answer_from_df(question, df)
        except Exception as e:
            last = e
    raise RuntimeError(f"Failed after {retries} tries: {last}")

# ────────────────────────────────────────────────
# Build evaluation dataset from CSV
# ────────────────────────────────────────────────
gold = pd.read_csv(CSV_GOLDSET)
samples = gold.sample(n=SAMPLE_SIZE, random_state=42)

def make_pair(row):
    q = f"What is the location of Equipment ID {row['Equipment ID']}?"
    return {"input": q, "ideal_output": str(row['Location'])}

dataset = EvaluationDataset([make_pair(r) for _, r in samples.iterrows()])

# ────────────────────────────────────────────────
# Metrics & instrumentation
# ────────────────────────────────────────────────
exact  = ExactMatchMetric(strict=False)
lat    = []
mem_mb = []

proc    = psutil.Process()
tracker = EmissionsTracker(output_file="energy.csv").start()

for sample in dataset:
    tracemalloc.start()
    t0 = time.perf_counter()

    answer = ask(sample["input"])

    dt = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    sample["model_output"] = answer
    sample["metadata"]     = {"latency_s": dt}

    lat.append(dt)
    mem_mb.append(peak / 1_048_576)

tracker.stop()
energy = pd.read_csv("energy.csv").iloc[-1]

# quality
result = evaluate(test_cases=dataset,metrics=[exact], raise_error=False, verbose=False)
acc    = result["ExactMatchMetric"]["score"]

# ────────────────────────────────────────────────
# Report
# ────────────────────────────────────────────────
print("\n=== BENCHMARK SUMMARY ===")
print(f"Questions evaluated  : {SAMPLE_SIZE}")
print(f"Exact-match accuracy : {acc:.2%}")
print(f"Mean latency (s)     : {sum(lat)/len(lat):.2f}")
print(f"Peak RAM per call MB : {max(mem_mb):.1f}")
print(f"Energy used (kWh)    : {energy['energy_consumed']:.6f}")
print(f"CO₂ emitted (kg)     : {energy['carbon_emitted']:.6f}")
