# app.py

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_babel import Babel, get_locale
import joblib
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
import json
import re
import google.generativeai as genai
import base64
from blueprints.auth import auth_bp
from models.user import db, User
from models.estimate import Estimate
from flask_login import LoginManager
from blueprints.dashboard import dashboard_bp
from blueprints.estimate import estimate_bp
# from blueprints.compare import compare_bp
from blueprints.shops import shops_bp
from blueprints.chat import chat_bp
from blueprints.admin import admin_bp
from blueprints.photo import photo_bp

# Blueprint imports (to be implemented in their respective folders)
# from blueprints.auth.routes import auth_bp
# from blueprints.dashboard.routes import dashboard_bp
# from blueprints.estimate.routes import estimate_bp
# from blueprints.photo.routes import photo_bp
# from blueprints.admin.routes import admin_bp
# from blueprints.compare.routes import compare_bp
# from blueprints.shops.routes import shops_bp
# from blueprints.chat.routes import chat_bp
# from blueprints.api.routes import api_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['LANGUAGES'] = ['en', 'fr', 'ar']
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
    db.init_app(app)

    def select_locale():
        if 'language' in session and session['language'] in app.config['LANGUAGES']:
            return session['language']
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    babel = Babel(app, locale_selector=select_locale)

    @app.context_processor
    def inject_locale():
        return dict(get_locale=get_locale)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    # Register blueprints (uncomment as implemented)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(estimate_bp)
    # app.register_blueprint(compare_bp)
    app.register_blueprint(shops_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(photo_bp)
    # app.register_blueprint(api_bp)

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/make_admin')
    def make_admin():
        from models.user import User, db
        user = User.query.filter_by(email='admin@gmail.com').first()
        if user:
            user.is_admin = True
            db.session.commit()
            return "Admin privileges granted!"
        return "User not found."

    @app.route('/language/<lang>')
    def set_language(lang=None):
        if lang in app.config['LANGUAGES']:
            session['language'] = lang
        return redirect(request.referrer or url_for('home'))

    return app

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDzVhetJLHiv357wc1X-0XgbbfYktqHO-c")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Load ML models
model_path = Path("gradient_boosting_model.pkl")
preprocessor_path = Path("preprocessor.pkl")
best_model = joblib.load(model_path)
preprocessor = joblib.load(preprocessor_path)

brands = ['Dacia', 'Renault', 'Peugeot', 'Hyundai', 'Volkswagen', 'Toyota', 'Fiat', 'Ford', 'Mercedes', 'BMW']
models = {
    'Dacia': ['Logan', 'Sandero', 'Duster'],
    'Renault': ['Clio', 'Megane', 'Kangoo'],
    'Peugeot': ['208', '301', '308'],
    'Hyundai': ['i10', 'i20', 'Tucson'],
    'Volkswagen': ['Polo', 'Golf', 'Passat'],
    'Toyota': ['Yaris', 'Corolla', 'RAV4'],
    'Fiat': ['Panda', 'Tipo', '500'],
    'Ford': ['Fiesta', 'Focus', 'EcoSport'],
    'Mercedes': ['C-Class', 'E-Class', 'A-Class'],
    'BMW': ['Series 1', 'Series 3', 'X1']
}
car_parts = ['Porte arrière gauche', 'Aile arrière droite', 'Aile arrière gauche', 'Pare-brise arrière', 'Coffre', 'Feu arrière droit', 'Feu arrière gauche', 'Pare-choc arrière', "Plaque d'immatriculation arrière", 'Pare-choc avant', 'Capot', 'Grille', 'Phare avant gauche', 'Phare avant droit']
car_parts_map = dict(zip(car_parts, car_parts))
severities = {1: 'Mineur (Rayures)', 2: 'Modéré (Bosses)', 3: 'Grave (Fissures, Cassures)'}
severity_descriptions = {
    1: "Rayures superficielles, éraflures mineures, petites écailles de peinture",
    2: "Bosses visibles, dommages partiels aux composants, rayures profondes",
    3: "Dommages structurels, composants cassés, fissures profondes nécessitant un remplacement complet"
}

def format_currency(amount):
    return f"{amount:,.2f} MAD"

def get_cost_category(cost):
    if cost < 1000:
            return "Bas", "��"
    elif cost < 3000:
        return "Moyen", "🟡"
    else:
        return "Élevé", "🔴"

def validate_input_data(brand, model_name, year, damaged_part, severity):
    if not brand or not model_name or not year or not damaged_part or not severity:
        return False, "Tous les champs sont obligatoires."
    try:
        year = int(year)
    except:
        return False, "L'année doit être un nombre."
    if year < 2005 or year > 2024:
        return False, "L'année doit être comprise entre 2005 et 2024."
    if brand not in brands:
        return False, "Marque non valide."
    if model_name not in models.get(brand, []):
        return False, "Modèle non valide."
    if damaged_part not in car_parts:
        return False, "Partie endommagée non valide."
    if int(severity) not in severities:
        return False, "Sévérité invalide."
    return True, ""

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
