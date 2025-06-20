# Car Repair Cost Estimator

This project provides multiple interfaces for estimating car repair costs using a pre‑trained machine learning model and AI image analysis.

## Contents

- **Streamlit app** (`app.py`) – original UI for manual entry or photo analysis
- **FastAPI backend** (`api.py`) exposing `/predict` and `/analyze` endpoints
- **React frontend** (`frontend/`) built with Vite and Material‑UI

## Setup

1. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file with your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key
   ```
3. (Optional) install Node dependencies for the React app *(requires internet access)*:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Running the Backend

Start the FastAPI server:

```bash
uvicorn api:app --reload
```

### API Endpoints

- `POST /predict` – send car details as JSON to get a cost estimate
- `POST /analyze` – upload an image (`file` field) to analyze damage and return an estimate

## Running the Streamlit App

You can still launch the original Streamlit interface:

```bash
streamlit run app.py
```

Both interfaces rely on the same trained model files (`gradient_boosting_model.pkl` and `preprocessor.pkl`).

