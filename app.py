from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# Load knowledge base for chatbot
def load_knowledge():
    try:
        with open('knowledge_base.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"intents": []}

@app.route('/')
def index():
    """Main page - test.html"""
    return render_template('test.html')

@app.route('/guide')
def guide():
    """Second main page - guide.html"""
    return render_template('guide.html')

@app.route('/about')
def about():
    """About page - empty for now"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')

# Chatbot API endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').lower()
    
    knowledge = load_knowledge()
    
    # Simple response matching
    for intent in knowledge.get('intents', []):
        for pattern in intent.get('patterns', []):
            if pattern.lower() in user_message:
                responses = intent.get('responses', [])
                if responses:
                    return jsonify({'response': responses[0]})
    
    return jsonify({'response': "I'm sorry, I don't understand. Please ask about campus locations, facilities, or directions."})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)