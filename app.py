from flask import Flask, request, jsonify, send_from_directory, session
from together import Together
import os

app = Flask(__name__)

# Configure secret key for session management
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

together_api_key = os.environ.get("TOGETHER_API_KEY")
client = Together(api_key=together_api_key)

@app.before_request
def clear_on_refresh():
    if request.endpoint == 'index':
        session.pop('messages', None)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    # Retrieve or initialize conversation history
    messages = session.get('messages', [])
    messages.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=messages
    )
    answer = response.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    session['messages'] = messages
    return jsonify({'answer': answer})

@app.route('/conversation')
def conversation():
    messages = session.get('messages', [])
    return jsonify({'messages': messages})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
