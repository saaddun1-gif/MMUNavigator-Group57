from flask import Flask, render_template

app = Flask(__name__)

@app.route('/pin_test')
def index():
    return render_template('pin_test.html')

if __name__ == '__main__':
    app.run(debug=True)