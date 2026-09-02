import requests


BASE_URL = "http://127.0.0.1:8001"


# ============================================================
# Base valid weather payload
# ============================================================

valid_weather = {
    "city": "Srinagar",
    "timestamp": "2026-09-01T10:00:00",

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
    "uv_index": 1.0,
    "pm2_5": 20.0,
    "pm10": 35.0,
    "nitrogen_dioxide": 10.0,
    "sulphur_dioxide": 5.0,
    "carbon_monoxide": 300.0,
    "ozone": 70.0,

    "sunrise": "2026-09-01T05:58",
    "sunset": "2026-09-01T18:55",
    "is_daylight": True
}


# ============================================================
# Helper
# ============================================================

def test_case(name, payload):

    response = requests.post(
        f"{BASE_URL}/personalize",
        json=payload
    )

    print("\n--------------------------------")
    print(name)
    print("--------------------------------")
    print("Status:", response.status_code)

    try:
        print("Response:", response.json())
    except Exception:
        print("Response:", response.text)

    return response


# ============================================================
# Test cases
# ============================================================

print("\n================================")
print("API ROBUSTNESS TEST")
print("================================")


# ------------------------------------------------------------
# 1. Valid request
# ------------------------------------------------------------

test_case(
    "VALID REQUEST",
    {
        "user_id": "robustness_user",
        "persona": "fitness",
        "weather": valid_weather
    }
)


# ------------------------------------------------------------
# 2. Missing user_id
# ------------------------------------------------------------

test_case(
    "MISSING USER ID",
    {
        "persona": "fitness",
        "weather": valid_weather
    }
)


# ------------------------------------------------------------
# 3. Missing persona
# ------------------------------------------------------------

test_case(
    "MISSING PERSONA",
    {
        "user_id": "robustness_user",
        "weather": valid_weather
    }
)


# ------------------------------------------------------------
# 4. Missing weather
# ------------------------------------------------------------

test_case(
    "MISSING WEATHER",
    {
        "user_id": "robustness_user",
        "persona": "fitness"
    }
)


# ------------------------------------------------------------
# 5. Invalid persona
# ------------------------------------------------------------

test_case(
    "INVALID PERSONA",
    {
        "user_id": "robustness_user",
        "persona": "pilot",
        "weather": valid_weather
    }
)


# ------------------------------------------------------------
# 6. Unknown user
# ------------------------------------------------------------

test_case(
    "UNKNOWN USER",
    {
        "user_id": "completely_new_user_999",
        "persona": "traveler",
        "weather": valid_weather
    }
)


# ------------------------------------------------------------
# 7. Empty weather
# ------------------------------------------------------------

test_case(
    "EMPTY WEATHER",
    {
        "user_id": "robustness_user",
        "persona": "fitness",
        "weather": {}
    }
)


print("\n================================")
print("ROBUSTNESS TEST COMPLETE")
print("================================")