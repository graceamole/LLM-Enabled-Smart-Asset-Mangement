from flask import Flask, request, jsonify, send_from_directory
from langchain_community.llms import HuggingFacePipeline
from langchain.sql_database import SQLDatabase
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import os

app = Flask(__name__, static_folder='../public', static_url_path='')

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

# -----------------------------
# 🤖 Load microsoft/phi-1_5 Model
# -----------------------------
model_name = "microsoft/phi-1_5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=256,
    temperature=0.3,
    top_k=50,
    top_p=0.95,
)

llm = HuggingFacePipeline(pipeline=pipe)

# -----------------------------
# 🗄️ Connect to SQLite Database
# -----------------------------
db = SQLDatabase.from_uri("sqlite:///app/assets_data.db", include_tables=["filled_asset_data"])
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    handle_parsing_errors=True  # ✅ Prevent LLM crashes
)

# -----------------------------
# 💬 Flask Route for Chat UI
# -----------------------------
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    try:
        response = agent_executor.run(user_input)

        # 👉 Format LLM result as pretty output
        if isinstance(response, str) and "\n" in response:
            lines = response.strip().split("\n")
            if len(lines) > 1 and "|" in lines[0]:
                # Table-like format
                response = "📊 Query Result:\n" + "\n".join(lines)
            else:
                # List format
                response = "📝 Summary:\n" + "\n".join(f"• {line}" for line in lines)

        return jsonify({'reply': response})

    except Exception as e:
        return jsonify({'reply': "❌ Sorry, I couldn't process that. Try rephrasing your question."})
