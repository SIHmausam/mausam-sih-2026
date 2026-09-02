import requests


BASE_URL = "http://127.0.0.1:8001"


weather = {
    "city": "Srinagar",
    "timestamp": "2026-09-01T10:30:00",

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


print("\n================================")
print("PERSONALIZATION CONTRACT TEST")
print("================================")


response = requests.post(
    f"{BASE_URL}/personalize",
    json={
        "user_id": "contract_test_user",
        "persona": "fitness",
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
assert "persona" in data
assert "cards" in data

assert data["city"] == "Srinagar"
assert data["persona"] == "fitness"


# ============================================================
# Personalization items
# ============================================================

items = data["cards"]

assert isinstance(items, list)
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


# ============================================================
# Ranking must be valid
# ============================================================

ranks = [item["rank"] for item in items]

assert ranks == list(range(1, 9))


scores = [item["score"] for item in items]

assert scores == sorted(scores, reverse=True)


print("\n================================")
print("CONTRACT VALIDATION")
print("================================")

print("City:", data["city"])
print("Persona:", data["persona"])
print("Items returned:", len(items))

print("\nTop priority:")
print("Information:", items[0]["card"])
print("Score:", items[0]["score"])
print("Insight:", items[0]["insight"])

print("\n================================")
print("UI-AGNOSTIC CONTRACT PASSED")
print("================================")