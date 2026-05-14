from flask import Flask, render_template

app = Flask(__name__, template_folder='template')  # ← SEE THE 'template_folder' PART

@app.route('/')
def home():
    return render_template('test.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin_login')
def admin_login():
    return render_template('Admin_Login.html')

@app.route('/landing')
def landing():
    return render_template('landing_page.html')

if __name__ == '__main__':
    app.run(debug=True)