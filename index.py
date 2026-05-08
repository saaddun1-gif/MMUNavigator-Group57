from flask import Flask, request, redirect, url_for

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['fpass']

    # Example validation (you can improve later)
    if email == "admin@mmu.edu.my" and password == "1234":
        return redirect("/admin")   # go to admin page
    else:
        return "Invalid login"