from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Main Public View
@app.route('/')
def index():
    return render_template('test.html') # Using your specific filename

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

if __name__ == '__main__':
    app.run(debug=True)