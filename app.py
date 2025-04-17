import streamlit as st
import joblib
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json
import re
from datetime import datetime
import base64
import os
from dotenv import load_dotenv

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

st.set_page_config(
    page_title="Estimateur de Coût de Réparation Auto Pro",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDzVhetJLHiv357wc1X-0XgbbfYktqHO-c")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@st.cache_resource
def load_models():
    try:
        best_model = joblib.load("gradient_boosting_model.pkl")
        preprocessor = joblib.load("preprocessor.pkl")
        return best_model, preprocessor
    except Exception as e:
        st.error(f"Erreur lors du chargement des modèles: {e}")
        return None, None

best_model, preprocessor = load_models()
if best_model is None or preprocessor is None:
    st.stop()

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
car_parts = ['Porte arriere gauche', 'Aile arriere droit', 'Aile arriere gauche', 'Pare-brise arriere', 'Malle', 'Feu arriere droit', 'Feu arriere gauche', 'Pare-choc arriere', 'Plaque immatriculation arriere', 'Pare-choc avant', 'Capot', 'Grille', 'Phare avant gauche', 'Phare avant droit']
car_parts_en = ['Left rear door', 'Right rear wing', 'Left rear wing', 'Rear windshield', 'Trunk', 'Right rear light', 'Left rear light', 'Rear bumper', 'Rear license plate', 'Front bumper', 'Hood', 'Grille', 'Left headlight', 'Right headlight']
car_parts_map = dict(zip(car_parts, car_parts_en))
severities = {1: 'Minor (Scratches)', 2: 'Moderate (Dents)', 3: 'Severe (Cracks, Breaks)'}
severity_descriptions = {
    1: "Surface scratches, minor scuffs, small paint chips",
    2: "Visible dents, partial component damage, deeper scratches",
    3: "Structural damage, broken components, deep cracks requiring complete replacement"
}

def format_currency(amount):
    return f"{amount:,.2f} MAD"

def get_cost_category(cost):
    if cost < 1000:
        return "Low", "🟢"
    elif cost < 3000:
        return "Medium", "🟡"
    else:
        return "High", "🔴"

def analyze_image_with_gemini(image):
    prompt = """
    Please analyze this car image and extract the following:
    - Car brand and model
    - Estimated year of manufacture
    - Damaged part
    - Severity of the damage (respond with a number: 1 for Minor, 2 for Moderate, 3 for Severe)
    - Brief description
    - Estimated repair cost in MAD

    Respond with JSON:
    {
        "brand": "...",
        "model": "...",
        "year": 2020,
        "damaged_part": "...",
        "severity": 1,
        "damage_description": "...",
        "estimated_cost": 2500
    }
    """
    try:
        # Convert PIL Image to bytes
        import io
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Create Gemini image part
        image_part = {"mime_type": "image/jpeg", "data": img_byte_arr}
        
        # Generate content
        response = model.generate_content([prompt, image_part])
        
        # Get the response text
        response_text = response.text
        
        # Find JSON in response
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
                # Convert severity to integer if it's not already
                if isinstance(result.get('severity'), str):
                    # Extract first number from severity string
                    severity_num = int(''.join(filter(str.isdigit, result['severity']))[:1])
                    result['severity'] = min(max(severity_num, 1), 3)  # Ensure between 1 and 3
                
                # Map English part names to French
                for fr, en in car_parts_map.items():
                    if result.get("damaged_part", "").lower() in en.lower():
                        result["damaged_part"] = fr
                        break
                
                # Ensure the brand is in our list
                if result.get('brand') not in brands:
                    result['brand'] = brands[0]
                
                return result
            except json.JSONDecodeError:
                st.error("Erreur de format dans la réponse de l'IA")
                return None
        return None
    except Exception as e:
        st.error(f"Erreur lors de l'analyse de l'image: {str(e)}")
        return None

st.markdown("<div class='main-header'>🚗 Analyseur de Dommages Auto Pro</div>", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

# Initialize default values
default_brand = brands[0]
default_model = models[default_brand][0]  # This will be the first model of the first brand
default_year = 2020
default_damaged_part = car_parts[0]
default_severity = 1

# Create tabs for different input methods
tab1, tab2 = st.tabs(["📝 Saisie Manuelle", "📸 Analyse par Photo"])

with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🚘 Détails du Véhicule</div>", unsafe_allow_html=True)
    
    # Vehicle Selection
    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox("Marque de Voiture", brands, index=brands.index(default_brand))
        model_name = st.selectbox("Modèle de Voiture", models[brand], index=0)
        year = st.number_input("Année de la Voiture", min_value=2005, max_value=2024, value=default_year)

    with col2:
        damaged_part = st.selectbox(
            "Partie Endommagée",
            car_parts,
            index=car_parts.index(default_damaged_part),
            format_func=lambda x: f"{x} ({car_parts_map.get(x, x)})"
        )
        severity = st.selectbox(
            "Sévérité des Dommages",
            options=list(severities.keys()),
            format_func=lambda x: severities[x],
            index=default_severity - 1
        )

    st.markdown(f"<div class='info-box'>{severity_descriptions[severity]}</div>", unsafe_allow_html=True)

    if st.button("Calculer le Coût de Réparation", key="calculate_btn", use_container_width=True):
        with st.spinner("Calcul du coût de réparation..."):
            input_data = pd.DataFrame([{
                'Brand': brand,
                'Model': model_name,
                'Year': year,
                'Damaged_Part': damaged_part,
                'Damage_Severity': severity
            }])

            try:
                input_encoded = preprocessor.transform(input_data)
                predicted_cost = best_model.predict(input_encoded)[0]

                parts_ratio = 0.4 if severity == 1 else 0.5 if severity == 2 else 0.6
                labor_hours = 2 if severity == 1 else 4 if severity == 2 else 7
                labor_cost = labor_hours * 150

                parts_cost = predicted_cost * parts_ratio
                painting_cost = predicted_cost - parts_cost - labor_cost

                if painting_cost < 0:
                    painting_cost = 0
                    total_fixed = parts_cost + labor_cost
                    if total_fixed > 0:
                        ratio = predicted_cost / total_fixed
                        parts_cost *= ratio
                        labor_cost *= ratio

                # Affichage des résultats
                st.markdown("### 💰 Estimation des Coûts")
                cost_category, emoji = get_cost_category(predicted_cost)
                cost_class = "cost-low" if predicted_cost < 1000 else "cost-medium" if predicted_cost < 3000 else "cost-high"
                st.markdown(f"<div class='highlight'><h2 class='{cost_class}'>{emoji} {format_currency(predicted_cost)}</h2></div>", unsafe_allow_html=True)

                # Détail des coûts
                st.markdown(f"""
                <div class='cost-breakdown'>
                    <div class='cost-item parts'>
                        <h3>Pièces</h3>
                        <p>{format_currency(parts_cost)}</p>
                    </div>
                    <div class='cost-item labor'>
                        <h3>Main d'œuvre</h3>
                        <p>{format_currency(labor_cost)}</p>
                    </div>
                    <div class='cost-item painting'>
                        <h3>Peinture</h3>
                        <p>{format_currency(painting_cost)}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Calendrier
                st.markdown("<div class='section-header'>⏱ Calendrier de Réparation</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="timeline">
                    <div class="timeline-item left">
                        <div class="timeline-content">
                            <h4>Évaluation Initiale</h4>
                            <p>1-2 heures</p>
                        </div>
                    </div>
                    <div class="timeline-item right">
                        <div class="timeline-content">
                            <h4>Commande des Pièces</h4>
                            <p>1-2 jours</p>
                        </div>
                    </div>
                    <div class="timeline-item left">
                        <div class="timeline-content">
                            <h4>Travaux de Réparation</h4>
                            <p>{labor_hours} heures</p>
                        </div>
                    </div>
                    <div class="timeline-item right">
                        <div class="timeline-content">
                            <h4>Inspection Finale</h4>
                            <p>1-2 heures</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erreur lors du calcul du coût: {e}")
    else:
        st.info("Remplissez les détails et cliquez sur 'Calculer le Coût de Réparation' pour obtenir une estimation")

    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📸 Analyse Automatique par Photo</div>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Téléchargez une photo du dommage", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        try:
            # Display the uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Image téléchargée", use_container_width=True)
            
            with st.spinner("Analyse de l'image en cours..."):
                # Convert the image for Gemini
                result = analyze_image_with_gemini(image)
                
                if result:
                    st.success("Analyse complétée!")
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### 🚗 Détails du Véhicule")
                        st.write(f"**Marque:** {result['brand']}")
                        st.write(f"**Modèle:** {result['model']}")
                        st.write(f"**Année:** {result['year']}")
                    
                    with col2:
                        st.markdown("### 🔍 Analyse des Dommages")
                        st.write(f"**Partie endommagée:** {result['damaged_part']}")
                        st.write(f"**Sévérité:** {result['severity']}")
                        st.write(f"**Description:** {result['damage_description']}")
                    
                    # Calculate cost using the ML model
                    try:
                        input_data = pd.DataFrame([{
                            'Brand': result['brand'],
                            'Model': result['model'],
                            'Year': result['year'],
                            'Damaged_Part': result['damaged_part'],
                            'Damage_Severity': int(result['severity'].split()[0]) if isinstance(result['severity'], str) else result['severity']
                        }])
                        
                        input_encoded = preprocessor.transform(input_data)
                        predicted_cost = best_model.predict(input_encoded)[0]
                        
                        st.markdown("### 💰 Estimation des Coûts")
                        cost_category, emoji = get_cost_category(predicted_cost)
                        cost_class = "cost-low" if predicted_cost < 1000 else "cost-medium" if predicted_cost < 3000 else "cost-high"
                        st.markdown(f"<div class='highlight'><h2 class='{cost_class}'>{emoji} {format_currency(predicted_cost)}</h2></div>", unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Erreur lors du calcul du coût: {e}")
                        st.write("Utilisez l'onglet 'Saisie Manuelle' pour une estimation précise.")
                else:
                    st.error("Impossible d'analyser l'image. Veuillez réessayer avec une autre photo ou utiliser la saisie manuelle.")
        except Exception as e:
            st.error(f"Erreur lors du traitement de l'image: {e}")
    else:
        st.info("Téléchargez une photo claire du dommage pour obtenir une estimation automatique.")
    
    st.markdown("</div>", unsafe_allow_html=True)
