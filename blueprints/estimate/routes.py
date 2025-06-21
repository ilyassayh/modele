from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from models.user import db
from models.estimate import Estimate
import joblib
import pandas as pd
from pathlib import Path

estimate_bp = Blueprint('estimate', __name__)

# Load ML model and preprocessor once
model_path = Path('gradient_boosting_model.pkl')
preprocessor_path = Path('preprocessor.pkl')
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

@estimate_bp.route('/estimate', methods=['GET', 'POST'])
@login_required
def estimate():
    result = None
    if request.method == 'POST':
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        damaged_part = request.form.get('damaged_part')
        severity = request.form.get('severity')
        try:
            input_data = pd.DataFrame([{
                'Brand': brand,
                'Model': model,
                'Year': int(year),
                'Damaged_Part': damaged_part,
                'Damage_Severity': int(severity)
            }])
            input_encoded = preprocessor.transform(input_data)
            predicted_cost = best_model.predict(input_encoded)[0]
            # Simple breakdown (example)
            parts_ratio = 0.4 if int(severity) == 1 else 0.5 if int(severity) == 2 else 0.6
            labor_hours = 2 if int(severity) == 1 else 4 if int(severity) == 2 else 7
            labor_cost = labor_hours * 150
            parts_cost = predicted_cost * parts_ratio
            painting_cost = predicted_cost - parts_cost - labor_cost
            if painting_cost < 0:
                painting_cost = 0
            result = {
                'brand': brand,
                'model': model,
                'year': year,
                'damaged_part': damaged_part,
                'severity': severity,
                'predicted_cost': f"{predicted_cost:.2f} MAD",
                'parts_cost': f"{parts_cost:.2f} MAD",
                'labor_cost': f"{labor_cost:.2f} MAD",
                'painting_cost': f"{painting_cost:.2f} MAD",
                'labor_hours': labor_hours
            }

            # Save to database
            new_estimate = Estimate(
                user_id=current_user.id,
                estimate_type='manual',
                car_brand=brand,
                car_model=model,
                car_year=int(year),
                damaged_part=damaged_part,
                severity=severity,
                predicted_cost=result['predicted_cost']
            )
            db.session.add(new_estimate)
            db.session.commit()

            flash('Prediction successful and saved to your history!', 'success')
        except Exception as e:
            flash(f'Error during prediction: {e}', 'danger')
    return render_template('estimate/estimate.html', result=result, models=models, brands=brands, car_parts=car_parts) 