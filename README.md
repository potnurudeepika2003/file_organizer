"""
# 🌐 AI-Based Internet Connectivity Optimizer
## 🚀 Predict • Optimize • Connect Smarter

An AI-powered web application built with Streamlit that predicts and optimizes network signal strength 
based on real-time parameters like location, weather, latency, and users online.

It uses a Random Forest Regressor model trained on historical data (signal_data.csv) and automates 
live input fetching using browser geolocation and OpenWeatherMap API — no manual data upload required.

---

## 🧠 Key Features

✅ Real-Time Signal Prediction: Automatically fetches current location, weather, and network stats.  
✅ ML-Driven Optimization: Uses a trained Random Forest model for accurate signal strength predictions.  
✅ Browser Integration: Detects user’s geolocation directly through Streamlit-Javascript.  
✅ Clean UI: Interactive Streamlit dashboard for easy insights and manual parameter tweaking.  
✅ Offline/Manual Mode: Option to enter values manually if geolocation or APIs fail.  
✅ Model Transparency: Includes encoded preprocessing (LabelEncoder for weather) and pickle-based model storage.

---

## 🧰 Installation Guide

### 2️⃣ Install Dependencies
pip install -r requirements.txt

### 3️⃣ Add Required Files
- model.pkl – Trained Random Forest model  
- encoder.pkl – LabelEncoder for weather data  
- .env – Your OpenWeatherMap API key (optional for manual mode)

Example .env:
OPENWEATHER_API_KEY=your_api_key_here

### 4️⃣ Run the App
streamlit run app.py

Then open the local URL shown in the terminal (e.g., http://localhost:8501)

---

## 📁 File Structure

AI-Internet-Connectivity-Optimizer/
│
├── app.py                 # Main Streamlit application  
├── model.pkl              # Trained RandomForestRegressor model  
├── encoder.pkl            # LabelEncoder for weather categories  
├── requirements.txt       # Dependencies  
├── README.md              # Project Documentation  
└── assets/
    ├── screenshots/       # UI Previews (optional)
    └── favicon.ico        # App icon (optional)

---

## ⚙️ How It Works

### 🔹 Fetch Live Data
- Fetches location coordinates from the browser using Streamlit-Javascript.  
- Retrieves current weather via the OpenWeatherMap API.  
- Measures latency & speed through local tests or user input.

### 🔹 Predict Signal Strength
- The Random Forest model predicts signal strength (0–100) using trained features.  
- Features used: latency, weather, users_online.

### 🔹 Visualize & Compare
- Streamlit dashboard shows predictions, confidence levels, and optimization suggestions.

---

## 📊 Model Training

Feature | Description  
---------|--------------  
latency | Network delay in ms  
weather | Weather condition (encoded)  
users_online | Active users sharing the network  
Target → signal_strength | Predicted connectivity strength  

**Training Snippet:**
```python
model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)
joblib.dump(model, "model.pkl")
