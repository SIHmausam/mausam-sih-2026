import requests
import json
from datetime import datetime


# ============================================================
# Configuration
# ============================================================

BASE_URL = "http://127.0.0.1:8000"

USER_ID = "learning_test_user"
PERSONA = "fitness"

SESSION_ID = "learning_session_001"


# ============================================================
# Weather data
# ============================================================

weather = {
    "city": "Srinagar",
    "timestamp": datetime.now().isoformat(),
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
# Get personalization
# ============================================================

def get_ranking():

    response = requests.post(
        f"{BASE_URL}/personalize",
        json={
            "user_id": USER_ID,
            "persona": PERSONA,
            "weather": weather
        }
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# Record interaction
# ============================================================

def record_interaction(card, position):

    response = requests.post(
        f"{BASE_URL}/interaction",
        json={
            "user_id": USER_ID,
            "card_id": card,
            "action": "expand",
            "timestamp": datetime.now().isoformat(),
            "position": position,
            "session_id": SESSION_ID
        }
    )

    response.raise_for_status()


# ============================================================
# Display ranking
# ============================================================

def print_ranking(title, data):

    print("\n================================")
    print(title)
    print("================================")

    for card in data["cards"]:

        print(
            f'{card["rank"]}. '
            f'{card["card"]:<20} '
            f'{card["score"]:.4f}'
        )


# ============================================================
# Test
# ============================================================

print("\n================================")
print("END-TO-END LEARNING TEST")
print("================================")


# ------------------------------------------------------------
# BEFORE
# ------------------------------------------------------------

before = get_ranking()

print_ranking(
    "BEFORE INTERACTIONS",
    before
)


# ------------------------------------------------------------
# Repeated user behavior
# ------------------------------------------------------------

print("\nRecording repeated UV interactions...")

for i in range(5):

    record_interaction(
        "uv",
        3
    )

    print(
        f"Interaction {i + 1}: UV expanded"
    )


# ------------------------------------------------------------
# AFTER
# ------------------------------------------------------------

after = get_ranking()

print_ranking(
    "AFTER INTERACTIONS",
    after
)


# ------------------------------------------------------------
# Compare
# ------------------------------------------------------------

before_uv = next(
    card
    for card in before["cards"]
    if card["card"] == "uv"
)

after_uv = next(
    card
    for card in after["cards"]
    if card["card"] == "uv"
)


print("\n================================")
print("LEARNING RESULT")
print("================================")

print(
    f"UV before: rank {before_uv['rank']}, "
    f"score {before_uv['score']:.4f}"
)

print(
    f"UV after : rank {after_uv['rank']}, "
    f"score {after_uv['score']:.4f}"
)

print(
    f"Score change: "
    f"{after_uv['score'] - before_uv['score']:+.4f}"
)

print("\nLearning loop completed.")