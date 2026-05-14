from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# ==========================================
# 🗺️ YOUR CODE (MAPS & LIVE GPS)
# ==========================================

# Main Public View
@app.route('/')
def index():
    return render_template('test.html') 

# Admin View
@app.route('/admin')
def admin():
    return render_template('admin.html')

# Location Receiver
@app.route('/live-location', methods=['POST'])
def receive_location():
    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')
    print(f"Update: Admin/User GPS is at {lat}, {lng}")
    return jsonify({"status": "received"})


# ==========================================
# 🔑 YOUR FRIEND'S CODE (LOGIN SYSTEM)
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check credentials
        if username == "admin" and password == "1234":
            # Right now it goes to dashboard.html
            return redirect(url_for('dashboard', user_name=username))
        else:
            return "<h1>Login Failed.</h1><a href='/login'>Try again</a>"

    return render_template('login.html')

@app.route('/dashboard/<user_name>')
def dashboard(user_name):
    return render_template('dashboard.html', user=user_name)


if __name__ == '__main__':
    app.run(debug=True)