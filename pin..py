from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/test_pin')
def index():
    # We return the template without needing to pass coordinates
    # The browser will handle finding the location itself
    return render_template('test_pin.html')

@app.route('/log_arrival', methods=['POST'])
def log_arrival():
    data = request.json
    print(f"Alert: User reached the pinned area! Data: {data}")
    return jsonify({"status": "received"})

if __name__ == '__main__':
    app.run(debug=True)