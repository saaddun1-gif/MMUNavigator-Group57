from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check credentials
        if username == "admin" and password == "1234":
            # redirect(url_for('name_of_function'))
            return redirect(url_for('dashboard', user_name=username))
        else:
            return "<h1>Login Failed.</h1><a href='/login'>Try again</a>"

    return render_template('login.html')

@app.route('/dashboard/<user_name>')
def dashboard(user_name):
    # This page only displays after a successful redirect
    return render_template('dashboard.html', user=user_name)

if __name__ == '__main__':
    app.run(debug=True)