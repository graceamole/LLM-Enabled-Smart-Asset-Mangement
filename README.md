#  Equipment Database Natural Language Query App

This project allows users to interact with a SQLite database of equipment data using natural language questions via a web interface powered by **Streamlit** and **LLMs**.

---

##  Features

- **Natural Language → SQL** conversion using Groq's LLaMA model
- **Streamlit-based Web UI** for querying and document retrieval
- **Document BLOB support** (images, PDFs, manuals)
- **LLM-generated responses** for easy interpretation
- **Secure SQL generation** with quoted identifiers and filtering

---

##  Project Structure

Project Structure

```bash
ChatBot/
├── app/
│   ├── assets_data.db            # Your SQLite database
│   ├── smatbotest_v.py           # Core logic (SQL generation, querying, LLMs)
│   ├── chatbot_ui_v.py             # Streamlit UI script
│   ├── fileuploadnew.py          # (Optional) File upload handler
├── requirements.txt              # All Python dependencies
├── README.md                     # This file
├── .gitignore                    # Files to ignore
```

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/LLM-Enabled-Smart-Asset-Management.git
```

### 2. Set Up Virtual Environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate
On Windows: venv\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Install Dependencies Add Your Groq API Key

Set an environment variable named GROQ_API_KEY

```bash
export GROQ_API_KEY="your_key_here"     # On Linux/macOS
set GROQ_API_KEY="your_key_here"        # On Windows CMD
$env:GROQ_API_KEY="your_key_here"       # On PowerShell
```

### 5. Run the App
```bash
streamlit run app/chatbit_ui.py
```
