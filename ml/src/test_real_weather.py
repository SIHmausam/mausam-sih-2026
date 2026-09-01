import requests
from datetime import datetime


BASE_URL = "http://127.0.0.1:8000"

USER_ID = "real_weather_test"
PERSONA = "fitness"


# ============================================================
# Simulated REAL weather API response
# Same structure as our collected weather data
# ============================================================

weather = {
    "temperature_2m": 22.4,
    "relative_humidity_2m": 68,
    "apparent_temperature": 22.8,
    "precipitation": 0.0,
    "rain": 0.0,
    "weather_code": 1,
    "wind_speed_10m": 6.4,
    "soil_moisture_0_to_7cm": 0.31,

    "timestamp": datetime.now().isoformat(),

    "european_aqi": 45,
    "us_aqi": 62,
    "uv_index": 1.2,
    "pm2_5": 15.4,
    "pm10": 28.1,
    "nitrogen_dioxide": 8.5,
    "sulphur_dioxide": 4.1,
    "carbon_monoxide": 260.0,
    "ozone": 72.0,

    "sunrise": "2026-09-01T05:58",
    "sunset": "2026-09-01T18:55",
    "is_daylight": True,

    "city": "Srinagar"
}


print("\n================================")
print("REAL WEATHER COMPATIBILITY TEST")
print("================================")

print("City:", weather["city"])
print("Timestamp:", weather["timestamp"])
print("Persona:", PERSONA)


response = requests.post(
    f"{BASE_URL}/personalize",
    json={
        "user_id": USER_ID,
        "persona": PERSONA,
        "weather": weather
    }
)


print("\nStatus code:", response.status_code)

response.raise_for_status()

data = response.json()


print("\n================================")
print("PERSONALIZED RESULT")
print("================================")

print("City:", data["city"])
print("Persona:", data["persona"])

for card in data["cards"]:

    print(
        f'{card["rank"]}. '
        f'{card["card"]:<20} '
        f'{card["score"]:.4f}'
    )

    print(
        f'   → {card["insight"]}'
    )


print("\n================================")
print("COMPATIBILITY TEST PASSED")
print("================================")