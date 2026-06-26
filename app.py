from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from flask_mail import Mail, Message
from flask_cors import CORS
import random
import json
from datetime import datetime, timedelta
import os

# Try to import networkx for indoor/outdoor path routing
try:
    import networkx as nx
except ImportError:
    nx = None

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'
CORS(app)

# Location of data files
KNOWLEDGE_FILE = 'knowledge_base.json'
MAP_DATA_FILE = 'fci-network.geojson'

# --- 1. Flask-Mail Configuration ---
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='AdminMap44@gmail.com', 
    MAIL_PASSWORD='sidhnrqcdzpdmggm' 
)
mail = Mail(app)

# --- 2. Admin Credentials ---
ADMIN_DATA = {
    "username": "XxsaadgamingpromaxxX",
    "password": "ismailbinmail",
    "email": "AdminMap44@gmail.com"
}

# ========== CORE AI CHATBOT FUNCTIONS ==========
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
    
    is_what_question = any(phrase in user_question_lower for phrase in ['what is', "what's", 'tell me about', 'meaning of', 'define'])
    is_where_question = any(phrase in user_question_lower for phrase in ['where is', "where's", 'location of', 'find', 'located'])
    
    best_match = None
    best_score = 0
    best_question = None
    
    print(f"\n🔍 DEBUG: User asked: '{user_question}'")
    
    for q in knowledge_base.get('questions', []):
        if is_what_question and q.get('intent') != 'definition':
            continue
        if is_where_question and q.get('intent') != 'location':
            continue
        
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
        
        if score > best_score and score >= 0.2:
            best_score = score
            best_match = q
            best_question = q['question']
            
    if best_match:
        print(f"🔍 Matched '{user_question}' with {best_score*100:.0f}% confidence → {best_question}")
        return best_question, best_match['answer']
    
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


# ========== MAP PATHFINDING UTILITIES ==========
def build_spatial_network():
    """Parses LineStrings and Points from fci-network.geojson and constructs 
    a multi-level cross-connected routing graph mapping floor planes."""
    G = nx.Graph() if nx else None
    if not G or not os.path.exists(MAP_DATA_FILE):
        return G

    try:
        with open(MAP_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Discover all explicit unique floor levels defined among indoor points
        levels = set()
        room_nodes = []
        
        for feature in data.get('features', []):
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            if geometry and geometry.get('type') == 'Point':
                coords = geometry.get('coordinates', [])
                if len(coords) >= 2:
                    lon, lat = float(coords[0]), float(coords[1])
                    lvl = properties.get('level', 'Level G')
                    levels.add(lvl)
                    if 'name' in properties:
                        room_nodes.append({
                            'name': properties['name'],
                            'coords': (lon, lat),
                            'level': lvl
                        })
        
        if not levels:
            levels = {'Level G', 'Level 1', 'Level 2', 'Level 3', 'Level 4'}
            
        # Organize levels sequentially to enable proper staircase/elevator vertical transitions
        levels_ordered = ['Level G', 'Level 1', 'Level 2', 'Level 3', 'Level 4']
        levels_ordered = [lvl for lvl in levels_ordered if lvl in levels]
        if not levels_ordered:
            levels_ordered = sorted(list(levels))

        # 1. Build the path corridor infrastructure independently for each floor
        for feature in data.get('features', []):
            geometry = feature.get('geometry', {})
            if geometry and geometry.get('type') == 'LineString':
                coords = geometry.get('coordinates', [])
                
                # Clone layout pathways for each indoor building floor level
                for lvl in levels_ordered:
                    for i in range(len(coords) - 1):
                        node_a = (float(coords[i][0]), float(coords[i][1]), lvl)
                        node_b = (float(coords[i+1][0]), float(coords[i+1][1]), lvl)
                        distance = ((node_a[0] - node_b[0])**2 + (node_a[1] - node_b[1])**2)**0.5
                        G.add_edge(node_a, node_b, weight=distance)

        # 2. Attach room vertices onto their respective level's corridor structures
        for room in room_nodes:
            lon, lat = room['coords']
            lvl = room['level']
            room_node = (lon, lat, lvl)
            
            closest_corr = None
            min_dist = float('inf')
            for node in G.nodes():
                if node[2] == lvl and node != room_node:
                    dist = ((node[0] - lon)**2 + (node[1] - lat)**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        closest_corr = node
            
            if closest_corr:
                G.add_edge(room_node, closest_corr, weight=min_dist)

        # 3. Securely bridge floating corridor layout gaps (missing vertex snaps) per level
        TOLERANCE = 0.0001  # Matches up to ~11 meters maximum gap distance
        nodes_by_level = {}
        for node in G.nodes():
            lvl = node[2]
            if lvl not in nodes_by_level:
                nodes_by_level[lvl] = []
            nodes_by_level[lvl].append(node)
            
        for lvl, nodes in nodes_by_level.items():
            for i, node_1 in enumerate(nodes):
                for node_2 in nodes[i+1:]:
                    dist = ((node_1[0] - node_2[0])**2 + (node_1[1] - node_2[1])**2)**0.5
                    if dist <= TOLERANCE and not G.has_edge(node_1, node_2):
                        G.add_edge(node_1, node_2, weight=dist)

        # 4. Synthesize vertical structural linkages (Elevators/Stairs) between consecutive levels
        for idx in range(len(levels_ordered) - 1):
            lvl_current = levels_ordered[idx]
            lvl_next = levels_ordered[idx+1]
            
            nodes_curr = nodes_by_level.get(lvl_current, [])
            nodes_next = nodes_by_level.get(lvl_next, [])
            
            for n_curr in nodes_curr:
                for n_next in nodes_next:
                    # Look for overlapping structural nodes matching vertically (within ~1 meter buffer)
                    dist_2d = ((n_curr[0] - n_next[0])**2 + (n_curr[1] - n_next[1])**2)**0.5
                    if dist_2d < 0.00001:
                        VERTICAL_TRAVEL_PENALTY = 0.0001
                        G.add_edge(n_curr, n_next, weight=VERTICAL_TRAVEL_PENALTY)
                        
    except Exception as e:
        print(f"⚠️ Error initializing tracking map network: {e}")
    return G

def snap_to_closest_path_node(graph, target_coord, target_level=None):
    """Finds the absolute closest network path point, filtering by floor level preference if provided"""
    target_lon, target_lat = float(target_coord[0]), float(target_coord[1])
    closest_node = None
    shortest_distance = float('inf')
    
    for node in graph.nodes():
        if target_level and node[2] != target_level:
            continue
        distance = ((node[0] - target_lon)**2 + (node[1] - target_lat)**2)**0.5
        if distance < shortest_distance:
            shortest_distance = distance
            closest_node = node
            
    # Fallback to absolute closest 2D node if no nodes match the target level filter
    if not closest_node and target_level:
        for node in graph.nodes():
            distance = ((node[0] - target_lon)**2 + (node[1] - target_lat)**2)**0.5
            if distance < shortest_distance:
                shortest_distance = distance
                closest_node = node
                
    return closest_node


# ========== CAMPUS MAP CORE ENDPOINTS ==========

@app.route('/api/map-data', methods=['GET'])
def get_map_data():
    """Serves raw GeoJSON layers directly to the Leaflet script"""
    if not os.path.exists(MAP_DATA_FILE):
        return jsonify({"status": "error", "message": f"{MAP_DATA_FILE} file missing on server"}), 404
        
    try:
        with open(MAP_DATA_FILE, 'r', encoding='utf-8') as f:
            geojson_content = json.load(f)
        return jsonify(geojson_content)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/route', methods=['GET'])
def calculate_campus_route():
    """Calculates tracking path arrays across indoor rooms and outer campus roads, aware of floor levels"""
    if not nx:
        return jsonify({"status": "error", "message": "NetworkX library not installed on host environment"}), 500

    start_lon = request.args.get('start_lon')
    start_lat = request.args.get('start_lat')
    end_lon = request.args.get('end_lon')
    end_lat = request.args.get('end_lat')
    
    # Optional level attributes to accurately anchor starting/ending positions indoors
    start_level = request.args.get('start_level')
    end_level = request.args.get('end_level')

    if not all([start_lon, start_lat, end_lon, end_lat]):
        return jsonify({"status": "error", "message": "Missing coordinate parameters"}), 400

    try:
        raw_start = (float(start_lon), float(start_lat))
        raw_end = (float(end_lon), float(end_lat))
        
        G = build_spatial_network()
        if len(G.nodes) == 0:
            return jsonify({"status": "error", "message": f"Map path network from {MAP_DATA_FILE} is empty or corrupt"}), 500

        snapped_start = snap_to_closest_path_node(G, raw_start, start_level)
        snapped_end = snap_to_closest_path_node(G, raw_end, end_level)

        if not snapped_start or not snapped_end:
            return jsonify({"status": "error", "message": "Unable to map coordinates onto network paths"}), 404

        computed_node_path = nx.shortest_path(G, source=snapped_start, target=snapped_end, weight='weight')
        
        # Formats path back to frontend with level metadata appended: [lat, lon, level]
        leaflet_ready_path = [[node[1], node[0], node[2]] for node in computed_node_path]

        return jsonify({
            "status": "success",
            "coordinates": leaflet_ready_path
        })

    except nx.NetworkXNoPath:
        return jsonify({"status": "error", "message": "Paths between indoor/outdoor sections are isolated"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


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
    try:
        data = request.json
        user_message = data.get('message', '')
        
        kb = load_knowledge_base(KNOWLEDGE_FILE)
        user_keywords = extract_keywords(user_message)
        user_question_lower = user_message.lower()
        
        is_what_question = any(phrase in user_question_lower for phrase in ['what is', "what's", 'tell me about', 'meaning of', 'define'])
        is_where_question = any(phrase in user_question_lower for phrase in ['where is', "where's", 'location of', 'find', 'located'])
        
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
    print("🤖 MMU Navigator - Server Initialization Engine")
    print("=" * 50)
    print(f"📍 Main Application Base: http://127.0.0.1:5000/")
    print(f"🗺️ Map Layer Data Feed:  http://127.0.0.1:5000/api/map-data")
    print(f"🛣️ Routing/Tracking Engine: http://127.0.0.1:5000/api/route")
    print(f"💬 Chat Engine Interface:  http://127.0.0.1:5000/chat")
    print(f"📚 Using Active Database:  {KNOWLEDGE_FILE}")
    print("🟢 Press Ctrl+C to safely close connection")
    print("=" * 50)
    
    app.run(debug=True, host='127.0.0.1', port=5000)