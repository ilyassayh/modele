from .user import db
from datetime import datetime

class Estimate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Common fields
    estimate_type = db.Column(db.String(50), nullable=False) # 'manual' or 'photo'
    predicted_cost = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Fields for manual estimate
    car_brand = db.Column(db.String(100))
    car_model = db.Column(db.String(100))
    car_year = db.Column(db.Integer)
    damaged_part = db.Column(db.String(100))
    severity = db.Column(db.String(100))

    # Fields for photo estimate
    photo_filename = db.Column(db.String(200))
    photo_analysis_data = db.Column(db.Text) # Storing JSON results as text

    user = db.relationship('User', backref=db.backref('estimates', lazy=True))

    def __repr__(self):
        return f'<Estimate {self.id} for User {self.user_id}>' 