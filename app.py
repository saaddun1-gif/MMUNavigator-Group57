from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from flask_mail import Mail, Message
from flask_cors import CORS
import random
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'
CORS(app)

# We need to tell the computer where the knowledge file is
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

# ========== KNOWLEDGE BASE UTILITIES ==========
def load_knowledge_base(file_path: str) -> dict:
    """Safely loads the knowledge base JSON, creating an empty template if it doesn't exist."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        default_kb = {
            "questions": [
                {
                    "question": "Where is the library?",
                    "synonyms": ["locate library", "find the library", "siti hasmah digital library"],
                    "answer": "The Siti Hasmah Digital Library is located right in the center of campus, next to the Central Lecture Complex (CLC)."
                },
                {
                    "question": "How to go to FCI?",
                    "synonyms": ["where is fci", "faculty of computing and informatics"],
                    "answer": "The Faculty of Computing and Informatics (FCI) is situated on the northwestern side of the campus loop, near the main lake."
                }
            ]
        }
        save_knowledge_base(file_path, default_kb)
        return default_kb

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError:
        # Fallback if file gets corrupted
        return {"questions": []}

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
    """Find best match using keyword extraction"""
    user_keywords = extract_keywords(user_question)
    
    if not user_keywords:
        return None
    
    best_match = None
    best_score = 0
    best_question = None
    
    for q in knowledge_base.get('questions', []):
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
        
        if score > best_score and score >= 0.3:
            best_score = score
            best_match = q
            best_question = q['question']
    
    if best_match:
        print(f"🔍 Matched with {best_score*100:.0f}% confidence")
        return best_question, best_match['answer']
    
    return None

# ========== BASIC VIEWS ROUTES ==========

@app.route('/')
@app.route('/public')
def index():
    """Main page - renders map interface"""
    return render_template('test.html')

@app.route('/guide')
def guide():
    """Guide sub-page"""
    return render_template('guide.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# --- Admin System Routes ---

@app.route('/Admin_Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() or {}
        if data.get('username') == ADMIN_DATA['username'] and data.get('password') == ADMIN_DATA['password']:
            otp = str(random.randint(100000, 999999))
            
            # Save the code and compute expiry time (2 minutes into the future)
            session['otp'] = otp
            session['otp_expiry'] = (datetime.now() + timedelta(minutes=2)).timestamp()
            
            try:
                msg = Message("Admin Login Verification", 
                              sender=app.config['MAIL_USERNAME'], 
                              recipients=[ADMIN_DATA['email']])
                msg.body = f"Your validation code is: {otp}"
                mail.send(msg)
                return jsonify({"status": "otp_sent"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    
    return render_template('Admin_Login.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json() or {}
    user_otp = data.get('otp')
    current_time = datetime.now().timestamp()
    
    # 1. Grab values safely out of session context
    saved_otp = session.get('otp')
    expiry_time = session.get('otp_expiry', 0)
    
    # 2. Server check: Has the OTP officially expired?
    if current_time > expiry_time:
        session.pop('otp', None)
        session.pop('otp_expiry', None)
        return jsonify({"status": "error", "message": "OTP has expired. Please log in again."}), 401
        
    # 3. Match the user's input with the saved OTP token
    if saved_otp and user_otp == saved_otp:
        session['logged_in'] = True
        session['role'] = 'admin'
        
        # Cleanup temporary keys upon a successful verification loop
        session.pop('otp', None)
        session.pop('otp_expiry', None)
        return jsonify({"status": "success", "redirect": url_for('admin')})
    
    return jsonify({"status": "error", "message": "Invalid OTP"}), 401

@app.route('/admin')
def admin():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/admin_login')
def admin_login():
    # Capitalized to match file 'Admin_Login.html'
    return render_template('Admin_Login.html')

# ========== CHATBOT API ENDPOINTS (UNIFIED KEYS) ==========

@app.route('/chat', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def chat_api_handler():
    """Unified handler supporting both endpoint addresses safely"""
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '')
        
        print(f"📩 Received: {user_message}")
        
        kb = load_knowledge_base(KNOWLEDGE_FILE)
        match = find_best_match_by_keywords(user_message, kb)
        
        if match:
            _, answer = match
            response_payload = {'reply': answer, 'response': answer}
            return jsonify(response_payload)
        else:
            fallback_text = "I don't know the answer to that question. Try asking where the library or FCI is!"
            return jsonify({'reply': fallback_text, 'response': fallback_text})
            
    except Exception as e:
        print(f"Error handling chat route: {e}")
        return jsonify({'reply': f"Error: {str(e)}", 'response': f"Error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 MMU Navigator AI Chatbot Server (Combined & Patched)")
    print("=" * 50)
    print(f"📍 Application Root: http://127.0.0.1:5000/")
    print(f"📍 Chat Gateway:     http://127.0.0.1:5000/api/chat")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)