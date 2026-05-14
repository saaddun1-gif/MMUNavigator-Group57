from flask import Flask, render_template, request, jsonify, session, url_for
from flask_mail import Mail, Message
import random
from datetime import datetime, timedelta

app = Flask(__name__)
# Keep this secret! It secures your session data.
app.secret_key = 'your_super_secret_key_here'

# 1. Flask-Mail Configuration
# NOTE: If using Gmail, you MUST use an "App Password"
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='hazyqnorashrafhelmy@gmail.com', 
    MAIL_PASSWORD='xdjnyhwfyqndcakk' 
)
mail = Mail(app)

# Your Admin Credentials
ADMIN_DATA = {
    "username": "XxsaadgamingpromaxxX",
    "password": "ismailbinmail",
    "email": "hazyqnorashrafhelmy@gmail.com"
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        
        # Check credentials
        if data.get('username') == ADMIN_DATA['username'] and data.get('password') == ADMIN_DATA['password']:
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Store OTP and Expiry (2 minutes) in the session
            session['otp'] = otp
            session['otp_expiry'] = (datetime.now() + timedelta(minutes=2)).timestamp()
            
            # Attempt to send the email
            try:
                msg = Message("Admin Login Verification", 
                              sender=app.config['MAIL_USERNAME'], 
                              recipients=[ADMIN_DATA['email']])
                msg.body = f"Your one-time login code is: {otp}. It will expire in 2 minutes."
                mail.send(msg)
                
                # Signal the JavaScript to show the OTP section
                return jsonify({"status": "otp_sent"})
            except Exception as e:
                print(f"Mail Error: {e}")
                return jsonify({"status": "error", "message": "Could not send email. Check server settings."}), 500
        
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401
    
    # GET request: Show the login page
    return render_template('login.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    user_otp = data.get('otp')
    
    # Validate session data
    current_time = datetime.now().timestamp()
    stored_otp = session.get('otp')
    expiry = session.get('otp_expiry')

    if stored_otp and expiry and current_time < expiry:
        if user_otp == stored_otp:
            # Success! Mark user as logged in
            session['logged_in'] = True
            # Clear sensitive OTP data from session
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            
            # Send the redirect URL back to JavaScript
            return jsonify({"status": "success", "redirect": url_for('dashboard', user_name=ADMIN_DATA['username'])})
        else:
            return jsonify({"status": "error", "message": "Incorrect OTP code."}), 401
    
    return jsonify({"status": "error", "message": "OTP has expired or is invalid. Please restart login."}), 401

@app.route('/dashboard/<user_name>')
def dashboard(user_name):
    # Security check: Don't let people bypass the login via URL
    if not session.get('logged_in'):
        return "Unauthorized Access", 401
    return render_template('dashboard.html', user=user_name)

if __name__ == '__main__':
    app.run(debug=True)