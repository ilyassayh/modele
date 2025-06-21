from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from models.user import db
from models.estimate import Estimate
import random
import google.generativeai as genai
from io import BytesIO
import base64
import json
import cv2
import numpy as np
from PIL import Image
import os
from datetime import datetime

photo_bp = Blueprint('photo', __name__)

# Load Gemini model (reuse configuration from app.py)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

def enhance_image_quality(image_bytes):
    """Enhance image quality for better AI analysis"""
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Apply image enhancement
        # 1. Denoise
        denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        
        # 2. Enhance contrast
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl,a,b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # 3. Sharpen
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Convert back to bytes
        _, buffer = cv2.imencode('.jpg', sharpened)
        return buffer.tobytes()
    except:
        return image_bytes

def analyze_car_details(image_bytes):
    """Analyze car brand, model, year, and color"""
    prompt = """
    Analyze this car image and provide detailed information in JSON format:
    {
        "brand": "car brand name",
        "model": "car model name", 
        "year": "estimated year (range)",
        "color": "car color",
        "confidence": 0.95
    }
    
    Be as specific as possible. If uncertain, provide ranges or "Unknown".
    """
    
    try:
        response = gemini_model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        # Extract JSON from response
        import re
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    
    return {
        "brand": "Unknown",
        "model": "Unknown", 
        "year": "Unknown",
        "color": "Unknown",
        "confidence": 0.0
    }

def detect_damage_areas(image_bytes):
    """Advanced damage detection with multiple areas"""
    prompt = """
    You are an expert automotive damage assessor. Analyze this car damage photo comprehensively.
    
    Provide a detailed JSON response with:
    {
        "damages": [
            {
                "part": "specific part name",
                "severity": 1-3 (1=minor, 2=moderate, 3=severe),
                "description": "detailed damage description",
                "confidence": 0.95,
                "location": "front/back/left/right side",
                "repair_type": "repair/replace/refinish",
                "estimated_labor_hours": 2.5,
                "parts_cost": 150.00,
                "labor_cost": 200.00
            }
        ],
        "overall_assessment": "summary of all damage",
        "repair_complexity": "simple/moderate/complex",
        "estimated_total_hours": 8.5,
        "safety_concerns": ["list any safety issues"],
        "recommendations": ["repair recommendations"]
    }
    
    Be thorough and accurate. Consider all visible damage areas.
    """
    
    try:
        response = gemini_model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        import re
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    
    return {"damages": [], "overall_assessment": "Analysis failed", "repair_complexity": "Unknown"}

def calculate_accurate_cost(damage_data, car_info):
    """Calculate more accurate repair costs based on damage and car info"""
    base_labor_rate = 85  # MAD per hour
    total_cost = 0
    detailed_costs = []
    
    for damage in damage_data.get('damages', []):
        # Base costs by severity
        severity_multipliers = {1: 0.8, 2: 1.5, 3: 2.5}
        base_cost = 500  # Base cost for minor damage
        
        # Calculate parts cost
        parts_cost = damage.get('parts_cost', base_cost * severity_multipliers.get(damage.get('severity', 1), 1))
        
        # Calculate labor cost
        labor_hours = damage.get('estimated_labor_hours', 2.0)
        labor_cost = labor_hours * base_labor_rate
        
        # Apply car brand adjustments
        brand_multipliers = {
            'BMW': 1.4, 'Mercedes': 1.3, 'Audi': 1.3,
            'Volkswagen': 1.1, 'Toyota': 1.0, 'Honda': 1.0,
            'Ford': 0.9, 'Renault': 0.9, 'Peugeot': 0.9
        }
        
        brand_multiplier = brand_multipliers.get(car_info.get('brand', '').upper(), 1.0)
        
        # Calculate total for this damage
        damage_total = (parts_cost + labor_cost) * brand_multiplier
        total_cost += damage_total
        
        detailed_costs.append({
            'part': damage.get('part', 'Unknown'),
            'severity': damage.get('severity', 1),
            'description': damage.get('description', ''),
            'parts_cost': parts_cost,
            'labor_cost': labor_cost,
            'total_cost': damage_total,
            'confidence': damage.get('confidence', 0.8),
            'repair_type': damage.get('repair_type', 'repair'),
            'labor_hours': labor_hours
        })
    
    return total_cost, detailed_costs

@photo_bp.route('/photo-analyze', methods=['GET', 'POST'])
@login_required
def photo_analyze():
    results = None
    if request.method == 'POST':
        files = request.files.getlist('photo')
        if not files or files[0].filename == '':
            flash('Please upload at least one photo.', 'danger')
        else:
            results = []
            for f in files:
                try:
                    # Read and enhance image
                    img_bytes = f.read()
                    enhanced_img = enhance_image_quality(img_bytes)
                    
                    # Analyze car details
                    car_info = analyze_car_details(enhanced_img)
                    
                    # Detect damage areas
                    damage_data = detect_damage_areas(enhanced_img)
                    
                    # Calculate accurate costs
                    total_cost, detailed_costs = calculate_accurate_cost(damage_data, car_info)
                    
                    # Prepare result
                    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                    
                    result_data = {
                        'filename': f.filename,
                        'car_info': car_info,
                        'damage_data': damage_data,
                        'detailed_costs': detailed_costs,
                        'total_estimated_cost': f"{total_cost:,.2f} MAD",
                        'img_data': img_b64,
                        'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'confidence_score': sum(d['confidence'] for d in detailed_costs) / len(detailed_costs) if detailed_costs else 0
                    }
                    
                    results.append(result_data)
                    
                    # Save to database
                    new_estimate = Estimate(
                        user_id=current_user.id,
                        estimate_type='photo_enhanced',
                        car_brand=car_info.get('brand', 'Unknown'),
                        car_model=car_info.get('model', 'Unknown'),
                        car_year=car_info.get('year', 'Unknown'),
                        damaged_part=", ".join([d['part'] for d in detailed_costs]),
                        predicted_cost=f"{total_cost:,.2f} MAD",
                        photo_filename=f.filename,
                        photo_analysis_data=json.dumps({
                            'car_info': car_info,
                            'damage_data': damage_data,
                            'detailed_costs': detailed_costs
                        })
                    )
                    db.session.add(new_estimate)
                    db.session.commit()
                    
                except Exception as e:
                    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                    results.append({
                        'filename': f.filename,
                        'error': str(e),
                        'img_data': img_b64
                    })
            
            flash(f'Successfully analyzed {len(results)} photo(s) with enhanced AI.', 'success')
    
    return render_template('photo/photo_analyze.html', results=results)

@photo_bp.route('/photo-analysis-history')
@login_required
def photo_analysis_history():
    """Show user's photo analysis history"""
    estimates = Estimate.query.filter_by(
        user_id=current_user.id, 
        estimate_type='photo_enhanced'
    ).order_by(Estimate.timestamp.desc()).all()
    today = datetime.utcnow().date()
    return render_template('photo/analysis_history.html', estimates=estimates, today=today)

@photo_bp.route('/api/analyze-photo', methods=['POST'])
@login_required
def api_analyze_photo():
    """API endpoint for real-time photo analysis"""
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo provided'}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        img_bytes = file.read()
        enhanced_img = enhance_image_quality(img_bytes)
        
        car_info = analyze_car_details(enhanced_img)
        damage_data = detect_damage_areas(enhanced_img)
        total_cost, detailed_costs = calculate_accurate_cost(damage_data, car_info)
        
        return jsonify({
            'success': True,
            'car_info': car_info,
            'damage_data': damage_data,
            'detailed_costs': detailed_costs,
            'total_cost': f"{total_cost:,.2f} MAD",
            'confidence_score': sum(d['confidence'] for d in detailed_costs) / len(detailed_costs) if detailed_costs else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 