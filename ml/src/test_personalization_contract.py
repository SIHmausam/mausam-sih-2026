import requests

BASE_URL = "http://127.0.0.1:8001"


weather = {
    "city": "Srinagar",
    "timestamp": "2026-09-01T10:30:00",

    # Weather
    "temperature_2m": 20.0,
    "relative_humidity_2m": 70.0,
    "dew_point_2m": 14.0,
    "apparent_temperature": 20.5,
    "precipitation": 0.0,
    "rain": 0.0,
    "weather_code": 0,
    "cloud_cover": 20.0,
    "wind_speed_10m": 5.0,
    "wind_direction_10m": 180.0,
    "wind_gusts_10m": 8.0,

    # Agriculture
    "soil_moisture_0_to_7cm": 0.30,
    "soil_moisture_7_to_28cm": 0.32,
    "soil_moisture_28_to_100cm": 0.35,
    "soil_moisture_100_to_255cm": 0.38,
    "soil_temperature_0_to_7cm": 18.0,
    "soil_temperature_7_to_28cm": 17.0,
    "soil_temperature_28_to_100cm": 16.0,
    "soil_temperature_100_to_255cm": 15.0,
    "et0_fao_evapotranspiration": 3.0,

    # Precipitation / forecast context
    "precipitation_hours": 0.0,
    "precipitation_probability": 10.0,
    "showers": 0.0,
    "visibility": 24000.0,

    # Air quality + UV
    "us_aqi": 80.0,
    "european_aqi": 50.0,
    "uv_index": 1.0,
    "uv_index_clear_sky": 2.0,
    "pm2_5": 20.0,
    "pm10": 35.0,
    "nitrogen_dioxide": 10.0,
    "sulphur_dioxide": 5.0,
    "carbon_monoxide": 300.0,
    "ozone": 70.0,

    # Marine unavailable for Srinagar
    "wave_height": None,
    "wave_direction": None,
    "wave_period": None,
    "swell_wave_height": None,
    "swell_wave_direction": None,
    "swell_wave_period": None,
    "sea_level_height_msl": None,
    "sea_surface_temperature": None,
    "marine_data_available": False,

    # Astronomy
    "sunrise": "2026-09-01T05:58",
    "sunset": "2026-09-01T18:55",
    "is_daylight": True
}


print("\n================================")
print("PHASE 2 PERSONALIZATION CONTRACT TEST")
print("================================")


response = requests.post(
    f"{BASE_URL}/personalize",
    json={
        "user_id": "contract_test_user",
        "personas": [
            "farmer",
            "health_conscious"
        ],
        "weather": weather
    }
)


print("Status code:", response.status_code)

response.raise_for_status()

data = response.json()


# ============================================================
# Top-level contract
# ============================================================

assert "city" in data
assert "personas" in data
assert "cards" in data

assert data["city"] == "Srinagar"

assert data["personas"] == [
    "farmer",
    "health_conscious"
]


# ============================================================
# Personalization items
# ============================================================

items = data["cards"]

assert isinstance(items, list)

# Farmer + Health Conscious union:
# temperature, weather_conditions, humidity,
# rain_forecast, wind, air_quality, uv_allergy,
# farm_garden
assert len(items) == 8


# ============================================================
# Each item must contain UI-independent information
# ============================================================

required_fields = [
    "rank",
    "card",
    "score",
    "insight"
]

for item in items:

    for field in required_fields:
        assert field in item, f"Missing field: {field}"

    assert isinstance(item["rank"], int)
    assert isinstance(item["card"], str)
    assert isinstance(item["score"], (int, float))
    assert isinstance(item["insight"], str)

    assert 0 <= item["score"] <= 1

    assert item["insight"].strip() != ""


# ============================================================
# Phase 2 card IDs
# ============================================================

allowed_cards = {
    "temperature",
    "weather_conditions",
    "humidity",
    "rain_forecast",
    "wind",
    "air_quality",
    "uv_allergy",
    "running_conditions",
    "surf_conditions",
    "tide_water",
    "farm_garden",
    "commute_conditions",
    "travel_conditions",
    "family_school",
    "event_conditions"
}

returned_cards = {
    item["card"]
    for item in items
}

assert returned_cards.issubset(
    allowed_cards
)


# ============================================================
# Ranking must be valid
# ============================================================

ranks = [
    item["rank"]
    for item in items
]

assert ranks == list(range(1, 9))


scores = [
    item["score"]
    for item in items
]

assert scores == sorted(
    scores,
    reverse=True
)


# ============================================================
# Marine gating
#
# Srinagar has no marine data, so surfer-only cards must
# never appear in this personalization response.
# ============================================================

assert "surf_conditions" not in returned_cards
assert "tide_water" not in returned_cards


print("\n================================")
print("CONTRACT VALIDATION")
print("================================")

print("City:", data["city"])
print("Personas:", data["personas"])
print("Items returned:", len(items))

print("\nTop priority:")
print("Card:", items[0]["card"])
print("Score:", items[0]["score"])
print("Insight:", items[0]["insight"])

print("\n================================")
print("PHASE 2 UI-AGNOSTIC CONTRACT PASSED")
print("================================")
