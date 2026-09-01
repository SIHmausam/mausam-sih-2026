import requests
from datetime import datetime


BASE_URL = "http://127.0.0.1:8000"

PERSONA = "fitness"


# ============================================================
# Different city/environment scenarios
# ============================================================

cities = {

    "Delhi": {
        "temperature_2m": 32.0,
        "relative_humidity_2m": 65,
        "apparent_temperature": 35.0,
        "precipitation": 0.0,
        "rain": 0.0,
        "weather_code": 1,
        "wind_speed_10m": 4.0,
        "soil_moisture_0_to_7cm": 0.25,
        "european_aqi": 140,
        "us_aqi": 190,
        "uv_index": 6.0,
        "pm2_5": 85.0,
        "pm10": 150.0,
        "nitrogen_dioxide": 45.0,
        "sulphur_dioxide": 12.0,
        "carbon_monoxide": 700.0,
        "ozone": 90.0,
        "is_daylight": True
    },

    "Srinagar": {
        "temperature_2m": 20.0,
        "relative_humidity_2m": 70,
        "apparent_temperature": 20.5,
        "precipitation": 0.0,
        "rain": 0.0,
        "weather_code": 1,
        "wind_speed_10m": 5.0,
        "soil_moisture_0_to_7cm": 0.30,
        "european_aqi": 45,
        "us_aqi": 62,
        "uv_index": 1.2,
        "pm2_5": 15.4,
        "pm10": 28.1,
        "nitrogen_dioxide": 8.5,
        "sulphur_dioxide": 4.1,
        "carbon_monoxide": 260.0,
        "ozone": 72.0,
        "is_daylight": True
    },

    "Dharamshala": {
        "temperature_2m": 17.0,
        "relative_humidity_2m": 88,
        "apparent_temperature": 17.5,
        "precipitation": 5.0,
        "rain": 5.0,
        "weather_code": 63,
        "wind_speed_10m": 10.0,
        "soil_moisture_0_to_7cm": 0.45,
        "european_aqi": 35,
        "us_aqi": 45,
        "uv_index": 0.8,
        "pm2_5": 10.0,
        "pm10": 20.0,
        "nitrogen_dioxide": 5.0,
        "sulphur_dioxide": 2.0,
        "carbon_monoxide": 200.0,
        "ozone": 65.0,
        "is_daylight": True
    },

    "Mumbai": {
        "temperature_2m": 29.0,
        "relative_humidity_2m": 84,
        "apparent_temperature": 34.0,
        "precipitation": 8.0,
        "rain": 8.0,
        "weather_code": 65,
        "wind_speed_10m": 12.0,
        "soil_moisture_0_to_7cm": 0.42,
        "european_aqi": 55,
        "us_aqi": 75,
        "uv_index": 3.0,
        "pm2_5": 25.0,
        "pm10": 45.0,
        "nitrogen_dioxide": 15.0,
        "sulphur_dioxide": 5.0,
        "carbon_monoxide": 300.0,
        "ozone": 80.0,
        "is_daylight": True
    }
}


# ============================================================
# Test
# ============================================================

print("\n================================")
print("MULTI-CITY CONTEXT VALIDATION")
print("================================")

print("Persona:", PERSONA)


for city, values in cities.items():

    weather = values.copy()

    weather["city"] = city
    weather["timestamp"] = datetime.now().isoformat()
    weather["sunrise"] = "2026-09-01T05:58"
    weather["sunset"] = "2026-09-01T18:55"

    response = requests.post(
        f"{BASE_URL}/personalize",
        json={
            "user_id": f"city_test_{city.lower()}",
            "persona": PERSONA,
            "weather": weather
        }
    )

    print("\n--------------------------------")
    print(city.upper())
    print("--------------------------------")

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
print("MULTI-CITY TEST COMPLETE")
print("================================")