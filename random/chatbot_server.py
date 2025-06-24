from flask import Flask, request, jsonify, send_from_directory
from smartbot import handle_question
import os

app = Flask(__name__, static_folder='public', static_url_path='')

# Route to serve HTML page
@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

# Route to handle chat input
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'reply': "Please enter a question."})

        print(f"🧠 User Question: {user_message}")
        
        # Use handle_question to get direct answer
        from smartbot import handle_question
        df, answer = handle_question(user_message)

        return jsonify({'reply': answer})

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({'reply': f"❌ Error: {str(e)}"})
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)