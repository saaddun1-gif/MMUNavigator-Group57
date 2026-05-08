from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from difflib import get_close_matches
import os

app = Flask(__name__)
CORS(app)

# Use your existing knowledge_base.json
KNOWLEDGE_FILE = 'knowledge_base.json'

# ========== THESE FUNCTIONS ARE FROM YOUR main.py ==========
def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        data: dict = json.load(file)
    return data

def find_best_match(user_question: str, knowledge_base: dict) -> str | None:
    user_question_lower = user_question.lower().strip()
    
    # Check main questions
    for q in knowledge_base['questions']:
        if q['question'].lower() == user_question_lower:
            return q['question']
    
    # Check synonyms
    for q in knowledge_base['questions']:
        if 'synonyms' in q:
            for synonym in q['synonyms']:
                if synonym.lower() == user_question_lower:
                    return q['question']
    
    # Fuzzy matching
    all_questions = [q['question'].lower() for q in knowledge_base['questions']]
    matches = get_close_matches(user_question_lower, all_questions, n=1, cutoff=0.6)
    
    if matches:
        return matches[0]
    
    return None

def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base['questions']:
        if q['question'].lower() == question.lower():
            return q['answer']
    return None
# ========== END OF main.py FUNCTIONS ==========

@app.route('/chat', methods=['POST'])
def chat():
    """This endpoint receives messages from your website"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        print(f"📩 Received: {user_message}")  # Debug in terminal
        
        # Load knowledge base
        kb = load_knowledge_base(KNOWLEDGE_FILE)
        
        # Find answer using your main.py logic
        best_match = find_best_match(user_message, kb)
        
        if best_match:
            answer = get_answer_for_question(best_match, kb)
            print(f"✅ Answer: {answer[:50]}...")
            return jsonify({'reply': answer})
        else:
            print("❌ No match found")
            return jsonify({'reply': "wat is this"})
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'reply': f"Error: {str(e)}"})

@app.route('/health', methods=['GET'])
def health():
    """Check if server is running"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 MMU Navigator AI Chatbot Server")
    print("=" * 50)
    print(f"📍 Website should connect to: http://localhost:5000")
    print(f"📚 Using: {KNOWLEDGE_FILE}")
    print("🟢 Press Ctrl+C to stop")
    print("=" * 50)
    app.run(debug=True, port=5000)