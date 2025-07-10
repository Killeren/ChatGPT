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

    # Step 1: Use chat API to infer if the prompt is for image generation
    system_prompt = {
        "role": "system",
        "content": (
            "You are an intent classifier. "
            "If the user's prompt is asking to generate, draw, or create an image, or describes a scene to visualize, respond with 'yes'. "
            "If the prompt is for a text answer or conversation, respond with 'no'. Respond with only 'yes' or 'no'."
        )
    }
    intent_response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[system_prompt, {"role": "user", "content": question}]
    )
    intent = intent_response.choices[0].message.content.strip().lower()

    if intent == 'yes':
        try:
            image_response = client.images.generate(
                prompt=question,
                model="black-forest-labs/FLUX.1-schnell-Free",
                steps=4,
                n=1
            )
            if image_response.data and image_response.data[0].url:
                image_url = image_response.data[0].url
                answer = "Here is your image:"
            else:
                image_url = None
                answer = "Sorry, I couldn't generate an image."
        except Exception as e:
            image_url = None
            if 'NSFW' in str(e) or 'nsfw' in str(e):
                answer = "Sorry, your image request was blocked because it may contain NSFW content."
            else:
                answer = f"Image generation failed: {str(e)}"
        messages.append({"role": "assistant", "content": answer, "image_url": image_url})
        session['messages'] = messages
        return jsonify({'answer': answer, 'image_url': image_url})
    else:
        # Otherwise, use chat completion for text
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
