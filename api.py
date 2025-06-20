from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
from PIL import Image
import io
import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    gemini_model = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

best_model = joblib.load("gradient_boosting_model.pkl")
preprocessor = joblib.load("preprocessor.pkl")

brands = ['Dacia', 'Renault', 'Peugeot', 'Hyundai', 'Volkswagen', 'Toyota', 'Fiat', 'Ford', 'Mercedes', 'BMW']
car_parts = ['Porte arrière gauche', 'Aile arrière droite', 'Aile arrière gauche', 'Pare-brise arrière', 'Coffre', 'Feu arrière droit', 'Feu arrière gauche', 'Pare-choc arrière', "Plaque d'immatriculation arrière", 'Pare-choc avant', 'Capot', 'Grille', 'Phare avant gauche', 'Phare avant droit']
car_parts_en = ['Left rear door', 'Right rear wing', 'Left rear wing', 'Rear windshield', 'Trunk', 'Right rear light', 'Left rear light', 'Rear bumper', 'Rear license plate', 'Front bumper', 'Hood', 'Grille', 'Left headlight', 'Right headlight']
car_parts_map = dict(zip(car_parts, car_parts_en))

class CarDetails(BaseModel):
    brand: str
    model: str
    year: int
    damaged_part: str
    severity: int


def analyze_image_with_gemini(image: Image.Image):
    if not gemini_model:
        raise RuntimeError("Gemini API key not configured")
    prompt = """
    Veuillez analyser cette image de voiture et extraire les informations suivantes :
    - Marque et modèle de la voiture
    - Année de fabrication estimée
    - Partie endommagée
    - Sévérité des dommages (répondez avec un nombre : 1 pour Mineur, 2 pour Modéré, 3 pour Grave)
    - Brève description

    Répondez en JSON :
    {
        "brand": "...",
        "model": "...",
        "year": 2020,
        "damaged_part": "...",
        "severity": 1,
        "damage_description": "..."
    }
    """
    img_bytes = io.BytesIO()
    image.save(img_bytes, format=image.format or 'JPEG')
    img_bytes = img_bytes.getvalue()
    image_part = {"mime_type": "image/jpeg", "data": img_bytes}
    response = gemini_model.generate_content([prompt, image_part])
    match = re.search(r"\{.*\}", response.text, re.DOTALL)
    if not match:
        raise RuntimeError("Invalid response from Gemini")
    result = json.loads(match.group(0))
    return result


@app.post("/predict")
def predict(details: CarDetails):
    data = pd.DataFrame([
        {
            "Brand": details.brand,
            "Model": details.model,
            "Year": details.year,
            "Damaged_Part": details.damaged_part,
            "Damage_Severity": details.severity,
        }
    ])
    encoded = preprocessor.transform(data)
    cost = best_model.predict(encoded)[0]
    return {"estimated_cost": float(cost)}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read()))
    result = analyze_image_with_gemini(image)
    # Compute cost with model
    data = pd.DataFrame([
        {
            "Brand": result["brand"],
            "Model": result["model"],
            "Year": int(result["year"]),
            "Damaged_Part": result["damaged_part"],
            "Damage_Severity": int(result["severity"]),
        }
    ])
    encoded = preprocessor.transform(data)
    cost = best_model.predict(encoded)[0]
    result["estimated_cost"] = float(cost)
    return result

