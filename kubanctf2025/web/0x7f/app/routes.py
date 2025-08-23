from flask import Blueprint, render_template, redirect, url_for, request
from app.models import User, db
from flask_login import login_user, login_required, logout_user, current_user
import jinja2

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def home():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('main.home'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

@main.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error = 'This username is already taken'
        else:
            hash = str(jinja2.Environment().from_string(password).render())
            user = User(username=username, password=hash)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('main.login'))
    return render_template('register.html', error=error)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))
