from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models.user import db, User
from flask_babel import _

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(_('Logged in successfully!'), 'success')
            return redirect(url_for('home'))
        else:
            flash(_('Invalid email or password.'), 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash(_('Passwords do not match.'), 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash(_('Email already registered.'), 'danger')
            return render_template('auth/register.html')
        hashed_pw = generate_password_hash(password)
        new_user = User(email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash(_('Registration successful! Please log in.'), 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'), 'info')
    return redirect(url_for('auth.login')) 