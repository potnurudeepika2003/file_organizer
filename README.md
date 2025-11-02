🌐 AI-Based Internet Connectivity Optimizer
🚀 Predict • Optimize • Connect Smarter

An AI-powered web application built with Streamlit that predicts and optimizes network signal strength based on real-time parameters like location, weather, latency, and users online.

It uses a Random Forest Regressor model trained on historical data (signal_data.csv) and automates live input fetching using browser geolocation and OpenWeatherMap API — no manual data upload required.

🧠 Key Features

✅ Real-Time Signal Prediction: Automatically fetches current location, weather, and network stats.

✅ ML-Driven Optimization: Uses a trained Random Forest model for accurate signal strength predictions.

✅ Browser Integration: Detects user’s geolocation directly through Streamlit-Javascript.

✅ Clean UI: Interactive Streamlit dashboard for easy insights and manual parameter tweaking.

✅ Offline/Manual Mode: Option to enter values manually if geolocation or APIs fail.

✅ Model Transparency: Includes encoded preprocessing (LabelEncoder for weather) and pickle-based model storage.

🧩 Tech Stack
Category	Technologies Used
Frontend / Dashboard	Streamlit, Streamlit-Javascript
Backend / ML Engine	Python, Scikit-Learn, Pandas, NumPy
Model	RandomForestRegressor
APIs	OpenWeatherMap (for weather data), Browser Geolocation
Deployment	Streamlit Cloud / Render / Netlify (with backend link)
🧰 Installation Guide
1️⃣ Clone or Download the Repo
git clone https://github.com/yourfriendusername/AI-Internet-Connectivity-Optimizer.git
cd AI-Internet-Connectivity-Optimizer

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Add Required Files

model.pkl – Trained Random Forest model

encoder.pkl – LabelEncoder for weather data

.env – Your OpenWeatherMap API key (optional for manual mode)

Example .env

OPENWEATHER_API_KEY=your_api_key_here

4️⃣ Run the App
streamlit run app.py


Then open the local URL shown in the terminal (e.g., http://localhost:8501
).

📁 File Structure
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

⚙️ How It Works

Fetch Live Data:

The app fetches location coordinates from the browser using Streamlit-Javascript.

It retrieves current weather via the OpenWeatherMap API.

It measures latency & speed through local tests or user input.

Predict Signal Strength:

The Random Forest model predicts the signal strength score (0–100) using trained features.

Features used: latency, weather, users_online.

Visualize & Compare:

Streamlit dashboard shows predictions, confidence levels, and optimization suggestions.

📊 Model Training

The Random Forest Regressor was trained on a simulated dataset:

Feature	Description
latency	Network delay in ms
weather	Weather condition (encoded)
users_online	Active users sharing the network
Target → signal_strength	Predicted connectivity strength

Training Snippet:

model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)
joblib.dump(model, "model.pkl")

🖼️ Screenshots
Dashboard	Prediction Example

	
🌤️ API Integration

OpenWeatherMap API Endpoint:

https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}


Sample Response:

{
  "weather": [{"main": "Clouds"}],
  "main": {"temp": 303.15},
  "name": "Hyderabad"
}

🔮 Future Enhancements

🔹 Integrate 5G signal prediction using real telecom datasets.

🔹 Add network-switching logic for real optimization (Wi-Fi ↔ Mobile).

🔹 Include time-series prediction for upcoming signal fluctuations.

🔹 Mobile PWA version for Android / iOS.

👨‍💻 Developer

👤 Sashi Vardhan Pragada

AI/ML Enthusiast | Full-Stack Developer | Data-Driven Thinker

🌍 Languages: English, Telugu, Hindi, Spanish

📧 Email: spragada2@gitam.in

💻 GitHub: github.com/sashivardhanpragada

🪄 Credits

Model Training: Custom Random Forest Model

APIs Used: OpenWeatherMap, Streamlit-Javascript

Inspiration: Need for intelligent, automated connectivity management

📜 License

This project is licensed under the MIT License — feel free to use, modify, and share it with attribution.

Would you like me to also make a README header section (with badges like Python version, Streamlit, License, and GitHub stars) like open-source projects have? It’ll make your repo look more professional.
