import os
from flask import Flask, request, jsonify, send_from_directory
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent

app = Flask(__name__, static_folder='../public', static_url_path='')

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

# -----------------------------------------------------
# 💡 Lazy loading variables (model and agent executor)
# -----------------------------------------------------
llm = None
agent_executor = None

# -----------------------------------------------------
# 🔁 One-time model + SQL agent initializer
# -----------------------------------------------------
def init_agent():
    global llm, agent_executor

    if agent_executor:
        return agent_executor  # Already loaded

    print("🚀 Loading microsoft/phi-1_5 model...")

    # Load tokenizer and model
    model_name = "microsoft/phi-1_5"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )

    # Build HuggingFace pipeline
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        temperature=0.3,
        top_k=50,
        top_p=0.95
    )

    # Wrap it in LangChain LLM interface
    llm = HuggingFacePipeline(pipeline=pipe)

    # Connect to your SQLite DB and toolkit
    db = SQLDatabase.from_uri("sqlite:///app/assets_data.db", include_tables=["filled_asset_data"])
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Provide a system-style prompt for better responses
    custom_prefix = (
        "You are a smart assistant answering questions using a SQLite table named 'filled_asset_data'.\n"
        "Use SQL to get correct data. Format answers in plain language or as simple tables.\n"
        "Examples:\n"
        "- Where is equipment EQ-3115?\n"
        "- List assets with confidence < 0.8\n"
        "- Count all reused assets\n\n"
        "Now answer this question:"
    )

    # Create SQL agent
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        handle_parsing_errors=True,
        prefix=custom_prefix
    )

    print("✅ Model + agent loaded and ready.")
    return agent_executor

# -----------------------------------------------------
# 💬 Chat endpoint for user questions
# -----------------------------------------------------
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    try:
        agent = init_agent()
        response = agent.invoke(user_input)

        # Clean up response formatting
        if isinstance(response, str) and "\n" in response:
            lines = response.strip().split("\n")
            if len(lines) > 1 and "|" in lines[0]:
                response = "Query Result:\n" + "\n".join(lines)
            else:
                response = " Summary:\n" + "\n".join(f"• {line}" for line in lines)

        print("Final Answer Answer to UI:", response)
        return jsonify({'reply': response})
        

    except Exception as e:
        print(" Error occurred:", str(e))
        return jsonify({'reply': f" Error: {str(e)}"})
