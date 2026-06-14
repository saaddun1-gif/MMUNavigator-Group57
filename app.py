from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from flask_mail import Mail, Message
from flask_cors import CORS
import random
import json
from datetime import datetime, timedelta
from difflib import get_close_matches
import os

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'
CORS(app)

# Location of the AI knowledge file
KNOWLEDGE_FILE = 'knowledge_base.json'

# --- 1. Flask-Mail Configuration ---
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='hazyqnorashrafhelmy@gmail.com', 
    MAIL_PASSWORD='xdjnyhwfyqndcakk' 
)
mail = Mail(app)

# --- 2. Admin Credentials ---
ADMIN_DATA = {
    "username": "XxsaadgamingpromaxxX",
    "password": "ismailbinmail",
    "email": "hazyqnorashrafhelmy@gmail.com"
}

# ========== CORE FUNCTIONS ==========
def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        data: dict = json.load(file)
    return data

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def extract_keywords(text: str) -> set:
    """Extract important keywords from user question"""
    stop_words = {'where', 'is', 'the', 'are', 'can', 'i', 'find', 'locate', 
                  'location', 'tell', 'me', 'how', 'to', 'go', 'get', 'do',
                  'you', 'know', 'what', 'which', 'way', 'at', 'of', 'in', 'on',
                  'a', 'an', 'and', 'or', 'but', 'for', 'with', 'without', 'by'}
    
    text_lower = text.lower()
    for char in '?.,!;:()[]{}':
        text_lower = text_lower.replace(char, '')
    
    words = set(text_lower.split())
    keywords = words - stop_words
    return keywords

def calculate_keyword_match(user_keywords: set, question_keywords: set) -> float:
    """Calculate how well user keywords match a question's keywords"""
    if not user_keywords or not question_keywords:
        return 0
    
    matches = user_keywords.intersection(question_keywords)
    match_count = len(matches)
    
    total_keywords = len(user_keywords.union(question_keywords))
    if total_keywords == 0:
        return 0
    
    score = match_count / total_keywords
    return score

def find_best_match_by_keywords(user_question: str, knowledge_base: dict) -> tuple | None:
    """Find best match using keyword extraction with intent detection"""
    user_question_lower = user_question.lower()
    user_keywords = extract_keywords(user_question)
    
    if not user_keywords:
        return None
    
    # Check for question type FIRST (this solves incorrect matching)
    is_what_question = any(phrase in user_question_lower for phrase in ['what is', 'what\'s', 'tell me about', 'meaning of', 'define'])
    is_where_question = any(phrase in user_question_lower for phrase in ['where is', 'where\'s', 'location of', 'find', 'located'])
    
    best_match = None
    best_score = 0
    best_question = None
    
    print(f"\n🔍 DEBUG: User asked: '{user_question}'")
    print(f"🔍 DEBUG: is_what_question = {is_what_question}")
    print(f"🔍 DEBUG: is_where_question = {is_where_question}")
    print(f"🔍 DEBUG: User keywords = {user_keywords}")
    
    # FIRST: Try to match by intent (STRICT filtering)
    for q in knowledge_base.get('questions', []):
        if is_what_question and q.get('intent') != 'definition':
            print(f"  📌 SKIPPING: '{q['question']}' (intent={q.get('intent')}) - not a definition")
            continue
        if is_where_question and q.get('intent') != 'location':
            print(f"  📌 SKIPPING: '{q['question']}' (intent={q.get('intent')}) - not a location")
            continue
        
        print(f"  ✅ CHECKING: '{q['question']}' (intent={q.get('intent')})")
        question_keywords = extract_keywords(q['question'])
        
        score = calculate_keyword_match(user_keywords, question_keywords)
        
        if 'synonyms' in q:
            for synonym in q['synonyms']:
                synonym_keywords = extract_keywords(synonym)
                synonym_score = calculate_keyword_match(user_keywords, synonym_keywords)
                if synonym_score > score:
                    score = synonym_score
        
        for keyword in user_keywords:
            if keyword in q['question'].lower():
                score += 0.1
        
        print(f"      📊 Score: {score:.2f}")
        
        if score > best_score and score >= 0.2:  # Lower threshold since intent matches
            best_score = score
            best_match = q
            best_question = q['question']
            
    if best_match:
        print(f"🔍 Matched '{user_question}' with {best_score*100:.0f}% confidence → {best_question}")
        return best_question, best_match['answer']
    
    # FALLBACK: If no intent match found, try matching generally
    print(f"⚠️ No intent match found, trying fallback matching...")
    for q in knowledge_base.get('questions', []):
        if q.get('intent') in ['definition', 'location'] and not is_what_question and not is_where_question:
            continue
            
        question_keywords = extract_keywords(q['question'])
        score = calculate_keyword_match(user_keywords, question_keywords)
        
        if 'synonyms' in q:
            for synonym in q['synonyms']:
                synonym_keywords = extract_keywords(synonym)
                synonym_score = calculate_keyword_match(user_keywords, synonym_keywords)
                if synonym_score > score:
                    score = synonym_score
        
        if score > best_score and score >= 0.3:
            best_score = score
            best_match = q
            best_question = q['question']
    
    if best_match:
        print(f"🔍 (Fallback) Matched '{user_question}' with {best_score*100:.0f}% confidence → {best_question}")
        return best_question, best_match['answer']
    
    return None

# ========== PAGE NAVIGATION ROUTES ==========

@app.route('/')
def index():
    return render_template('test.html')

@app.route('/public')
def public_view():
    return render_template('test.html') 

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ========== ADMIN LOGIN SECURITY SYSTEM ==========

@app.route('/Admin_Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        if data.get('username') == ADMIN_DATA['username'] and data.get('password') == ADMIN_DATA['password']:
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['otp_expiry'] = (datetime.now() + timedelta(minutes=2)).timestamp()
            
            try:
                msg = Message("Admin Login Verification", 
                              sender=app.config['MAIL_USERNAME'], 
                              recipients=[ADMIN_DATA['email']])
                msg.body = f"Your code is: {otp}"
                mail.send(msg)
                return jsonify({"status": "otp_sent"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    
    return render_template('Admin_Login.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    user_otp = data.get('otp')
    current_time = datetime.now().timestamp()
    
    if session.get('otp') and current_time < session.get('otp_expiry', 0):
        if user_otp == session['otp']:
            session['logged_in'] = True
            session['role'] = 'admin'
            session.pop('otp', None)
            return jsonify({"status": "success", "redirect": url_for('admin')})
    
    return jsonify({"status": "error", "message": "Invalid or expired OTP"}), 401

@app.route('/admin')
def admin():
    if not session.get('logged_in') or session.get('role') == 'guest':
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')

# ========== AI CHATBOT SYSTEM ENDPOINTS ==========

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint for standard message response formats"""
    try:
        data = request.json
        user_message = data.get('message', '')
        print(f"📩 Received: {user_message}")
        
        kb = load_knowledge_base(KNOWLEDGE_FILE)
        match = find_best_match_by_keywords(user_message, kb)
        
        if match:
            question, answer = match
            print(f"✅ Matched: {question}")
            return jsonify({'reply': answer})
        else:
            print("❌ No match found")
            return jsonify({'reply': "I don't know the answer to that question."})
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'reply': f"Error: {str(e)}"})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint for api data response formats"""
    try:
        data = request.json
        user_message = data.get('message', '')
        print(f"📩 Received: {user_message}")
        
        kb = load_knowledge_base(KNOWLEDGE_FILE)
        match = find_best_match_by_keywords(user_message, kb)
        
        if match:
            question, answer = match
            print(f"✅ Matched: {question}")
            return jsonify({'response': answer})
        else:
            print("❌ No match found")
            return jsonify({'response': "I don't know the answer to that question."})
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'response': f"Error: {str(e)}"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/debug/match', methods=['POST'])
def debug_match():
    """Debug tracker to check calculations in real-time"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        kb = load_knowledge_base(KNOWLEDGE_FILE)
        user_keywords = extract_keywords(user_message)
        user_question_lower = user_message.lower()
        
        is_what_question = any(phrase in user_question_lower for phrase in ['what is', 'what\'s', 'tell me about', 'meaning of', 'define'])
        is_where_question = any(phrase in user_question_lower for phrase in ['where is', 'where\'s', 'location of', 'find', 'located'])
        
        results = []
        for q in kb.get('questions', []):
            question_keywords = extract_keywords(q['question'])
            score = calculate_keyword_match(user_keywords, question_keywords)
            
            would_skip = False
            skip_reason = None
            if is_what_question and q.get('intent') == 'location':
                would_skip = True
                skip_reason = "not a definition question"
            if is_where_question and q.get('intent') == 'definition':
                would_skip = True
                skip_reason = "not a location question"
            
            results.append({
                'question': q['question'],
                'score': score,
                'intent': q.get('intent', 'unknown'),
                'would_be_skipped': would_skip,
                'skip_reason': skip_reason
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return jsonify({
            'user_question': user_message,
            'detected_what_question': is_what_question,
            'detected_where_question': is_where_question,
            'user_keywords': list(user_keywords),
            'matches': results
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 MMU Navigator AI Chatbot Server")
    print("=" * 50)
    print(f"📍 Main page: http://127.0.0.1:5000/")
    print(f"📍 Chat endpoint (/chat): http://127.0.0.1:5000/chat")
    print(f"📍 Chat endpoint (/api/chat): http://127.0.0.1:5000/api/chat")
    print(f"📍 Debug checker: http://127.0.0.1:5000/debug/match")
    print(f"📍 Health check: http://127.0.0.1:5000/health")
    print(f"📚 Using database: {KNOWLEDGE_FILE}")
    print("🟢 Press Ctrl+C to stop server")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)