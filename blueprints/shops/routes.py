from flask import Blueprint, render_template
from flask_login import login_required

shops_bp = Blueprint('shops', __name__)

@shops_bp.route('/shops', methods=['GET'])
@login_required
def shops():
    # Placeholder: mock shop data
    shop_list = [
        {'name': 'AutoFix Center', 'address': '123 Main St', 'phone': '555-1234'},
        {'name': 'CarCare Garage', 'address': '456 Elm Ave', 'phone': '555-5678'},
        {'name': 'ProRepair Workshop', 'address': '789 Oak Blvd', 'phone': '555-9012'}
    ]
    return render_template('shops/shops.html', shop_list=shop_list) 