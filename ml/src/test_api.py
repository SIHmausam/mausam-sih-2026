import requests
import pandas as pd


# ============================================================
# Configuration
# ============================================================

API_URL = "http://127.0.0.1:8001/personalize"

DATA_FILE = "data/processed/test.csv"


# ============================================================
# Load sample weather data
# ============================================================

df = pd.read_csv(DATA_FILE)

sample = df.iloc[0]


# ============================================================
# Build weather payload
# ============================================================

weather = {
    "city": str(sample["city"]),
    "timestamp": "2026-08-30 00:00:00",
    "temperature_2m": float(sample["temperature_2m"]),
    "relative_humidity_2m": int(sample["relative_humidity_2m"]),
    "apparent_temperature": float(sample["apparent_temperature"]),
    "precipitation": float(sample["precipitation"]),
    "rain": float(sample["rain"]),
    "weather_code": int(sample["weather_code"]),
    "wind_speed_10m": float(sample["wind_speed_10m"]),
    "soil_moisture_0_to_7cm": float(sample["soil_moisture_0_to_7cm"]),
    "us_aqi": int(sample["us_aqi"]),
    "european_aqi": int(sample["european_aqi"]),
    "uv_index": float(sample["uv_index"]),
    "pm2_5": float(sample["pm2_5"]),
    "pm10": float(sample["pm10"]),
    "nitrogen_dioxide": float(sample["nitrogen_dioxide"]),
    "sulphur_dioxide": float(sample["sulphur_dioxide"]),
    "carbon_monoxide": float(sample["carbon_monoxide"]),
    "ozone": float(sample["ozone"]),
    "is_daylight": bool(sample["is_daylight"])
}


# ============================================================
# Example user
# ============================================================

persona = "farmer"


# ============================================================
# Example interaction history
# ============================================================

interactions = [

    {
        "user_id": "user_001",
        "card_id": "soil_moisture",
        "action": "expand",
        "timestamp": "2026-08-31 09:00:00",
        "position": 1,
        "session_id": "session_001"
    },

    {
        "user_id": "user_001",
        "card_id": "soil_moisture",
        "action": "click",
        "timestamp": "2026-08-31 09:05:00",
        "position": 1,
        "session_id": "session_001"
    },

    {
        "user_id": "user_001",
        "card_id": "rain",
        "action": "expand",
        "timestamp": "2026-08-31 09:10:00",
        "position": 2,
        "session_id": "session_001"
    }

]


# ============================================================
# Request payload
# ============================================================

payload = {
    "weather": weather,
    "persona": persona,
    "interactions": interactions
}


# ============================================================
# Send request
# ============================================================

print("\n================================")
print("API PERSONALIZATION TEST")
print("================================")

print("Sending request...")

response = requests.post(
    API_URL,
    json=payload
)


# ============================================================
# Display result
# ============================================================

print("\nStatus code:", response.status_code)

print("\nResponse:")

print(
    response.text
)