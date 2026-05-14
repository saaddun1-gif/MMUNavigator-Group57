from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# 1. LANDING PAGE (First thing you see when running terminal)
@app.route('/')
def landing():
    return render_template('about.html') # You need to create this file

# 2. PUBLIC USER VIEW
@app.route('/public')
def public_view():
    return render_template('test.html') 

# 3. ADMIN VIEW
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

# 4. LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check credentials
        if username == "admin" and password == "1234":
            # SUCCESS -> Directly go to Admin Map!
            return redirect(url_for('admin'))
        else:
            return "<h1>Login Failed.</h1><a href='/login'>Try again</a>"

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)