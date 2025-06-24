from flask import Flask, request , jsonify , send_from_directory
app = Flask(__name__, static_folder='../public', static_url_path='')

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    return jsonify({'reply': f'You said: {user_input}'}) 