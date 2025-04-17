<<<<<<< HEAD
# Car Repair Cost Estimator

A Streamlit web application that estimates car repair costs using machine learning and AI image analysis.

## Features

- Manual cost estimation based on car details and damage severity
- AI-powered image analysis using Google Gemini
- Detailed cost breakdown (parts, labor, painting)
- Repair timeline estimation
- Multi-language support (French/English)

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Running the Application

1. Activate your virtual environment
2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Deployment Options

### Option 1: Streamlit Cloud (Recommended)
1. Create a Streamlit Cloud account
2. Connect your GitHub repository
3. Set environment variables (GEMINI_API_KEY)
4. Deploy

### Option 2: Heroku
1. Create a `Procfile`:
   ```
   web: streamlit run app.py --server.port $PORT
   ```
2. Deploy using Heroku CLI

### Option 3: Local Server
1. Install required packages
2. Run the application
3. Use ngrok or similar to expose the local server

## Model Files
- `gradient_boosting_model.pkl`: Trained machine learning model
- `preprocessor.pkl`: Data preprocessing pipeline

## Note
Make sure to keep your API keys secure and never commit them to version control. 
=======
# modele
 "Car Repair Cost Estimator - A Streamlit web application using machine learning and AI image analysis"
>>>>>>> origin/main
