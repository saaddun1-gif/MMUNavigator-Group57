from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['XxsaadgamersxX'] = '1233445' 

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

#DATABASE MODELS

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) 

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ROUTES

@app.route('/')
def home():
    return "<h1>Home Page</h1><p>Go to /login or /admin</p>"

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403) # Forbidden
    
    products = Product.query.all()
    return f"Welcome Admin {current_user.username}! There are {len(products)} products in the DB."

#DATABASE INITIALISATION

def create_admin():
    """Helper function to create a dummy admin if the DB is empty"""
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('12345')
        admin_user = User(username='Saad', password=hashed_pw, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: user='Saad', pw='12345'")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)