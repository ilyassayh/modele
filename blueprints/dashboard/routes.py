from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.estimate import Estimate
import re

dashboard_bp = Blueprint('dashboard', __name__)
 
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    estimates = Estimate.query.filter_by(user_id=current_user.id).order_by(Estimate.timestamp.desc()).all()
    
    total_estimates = len(estimates)
    average_cost = 0
    if total_estimates > 0:
        total_cost = 0
        valid_estimates = 0
        for est in estimates:
            # Extract numbers from the cost string e.g. "1500.00 MAD" -> 1500.00
            cost_str = est.predicted_cost or "0"
            cost_val = re.findall(r'\\d+\\.?\\d*', cost_str)
            if cost_val:
                total_cost += float(cost_val[0])
                valid_estimates += 1
        if valid_estimates > 0:
            average_cost = total_cost / valid_estimates

    stats = {
        'total_estimates': total_estimates,
        'average_cost': f"{average_cost:.2f} MAD"
    }

    return render_template('dashboard/dashboard.html', user=current_user, estimates=estimates, stats=stats) 