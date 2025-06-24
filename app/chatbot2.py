from flask import Flask, request, jsonify, send_from_directory
from langchain.llms import HuggingFacePipeline
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

# Load lightweight local LLM
model_name = "sshleifer/tiny-gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=128)
llm = HuggingFacePipeline(pipeline=pipe)

# Connect LangChain to your asset_data table
db = SQLDatabase.from_uri("sqlite:///app/assets_data.db", include_tables=["filled_asset_data"])
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True)

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    try:
        response = agent_executor.run(user_input)
        return jsonify({'reply': response})
    except Exception as e:
        return jsonify({'reply': f"⚠️ Error: {str(e)}"})
