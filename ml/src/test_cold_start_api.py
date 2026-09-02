import requests
from datetime import datetime


# ============================================================
# Configuration
# ============================================================

BASE_URL = "http://127.0.0.1:8001"

USER_ID = "brand_new_user"

TIMESTAMP = datetime.now().isoformat()


# ============================================================
# Weather data
# ============================================================

weather = {
    "city": "Srinagar",
    "timestamp": TIMESTAMP,
    "temperature_2m": 20.0,
    "relative_humidity_2m": 70,
    "apparent_temperature": 20.5,
    "precipitation": 0.0,
    "rain": 0.0,
    "weather_code": 0,
    "wind_speed_10m": 5.0,
    "soil_moisture_0_to_7cm": 0.30,
    "us_aqi": 80,
    "european_aqi": 50,
    "uv_index": 0.0,
    "pm2_5": 20.0,
    "pm10": 35.0,
    "nitrogen_dioxide": 10.0,
    "sulphur_dioxide": 5.0,
    "carbon_monoxide": 300.0,
    "ozone": 70.0,
    "sunrise": "2026-09-01T05:58",
    "sunset": "2026-09-01T18:55",
    "is_daylight": False
}


# ============================================================
# Test each persona
# ============================================================

personas = [
    "fitness",
    "farmer",
    "traveler"
]


print("\n================================")
print("COLD-START API VALIDATION")
print("================================")

print("\nUser:", USER_ID)
print("Interactions: 0")
print("City: Srinagar")


for persona in personas:

    print("\n--------------------------------")
    print(persona.upper(), "USER")
    print("--------------------------------")

    response = requests.post(
        f"{BASE_URL}/personalize",
        json={
            "user_id": USER_ID,
            "persona": persona,
            "weather": weather
        }
    )

    print("Status code:", response.status_code)

    response.raise_for_status()

    data = response.json()

    for card in data["cards"]:

        print(
            f'{card["rank"]}. '
            f'{card["card"]:<20} '
            f'{card["score"]:.4f}'
        )


print("\n================================")
print("COLD-START TEST COMPLETE")
print("================================")