from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from flask_mail import Mail, Message
import random
from datetime import datetime, timedelta

app = Flask(__name__)
# This is like a secret password for your website's memory
app.secret_key = 'your_super_secret_key_here'

# --- 1. Flask-Mail Configuration ---
# This part helps the computer send emails
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

# --- 3. Public & Landing Routes ---

@app.route('/')
def index(): # <--- Changed from 'landing' to 'index' to fix the error
    """Renders about.html as the primary landing page."""
    return render_template('test.html')

@app.route('/public')
def public_view():
    """Renders the map view (test.html)."""
    return render_template('test.html') 

# --- 4. Admin Login System ---

@app.route('/Admin_Login', methods=['GET', 'POST'])
def login():
    """Handles showing the login page and the AJAX POST request."""
    if request.method == 'POST':
        data = request.get_json()
        
        # Checking if the username and password match our secret list
        if data.get('username') == ADMIN_DATA['username'] and data.get('password') == ADMIN_DATA['password']:
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['otp_expiry'] = (datetime.now() + timedelta(minutes=2)).timestamp()
            
            try:
                # Sending the secret code to your email
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
    """Verifies the 6-digit code sent to email."""
    data = request.get_json()
    user_otp = data.get('otp')
    current_time = datetime.now().timestamp()
    
    # Check if the code is correct and not too old
    if session.get('otp') and current_time < session.get('otp_expiry', 0):
        if user_otp == session['otp']:
            session['logged_in'] = True
            session['role'] = 'admin'
            session.pop('otp', None) # Remove the code after it's used
            return jsonify({"status": "success", "redirect": url_for('admin')})
    
    return jsonify({"status": "error", "message": "Invalid or expired OTP"}), 401

@app.route('/admin')
def admin():
    """Protected Admin View."""
    # If the user is not logged in, kick them back to the login page
    if not session.get('logged_in') or session.get('role') == 'guest':
        return redirect(url_for('login'))
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)