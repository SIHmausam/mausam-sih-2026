import pandas as pd

from src.prediction_service import get_personalized_ranking


# ============================================================
# Load current conditions
# ============================================================

DATA_FILE = "data/processed/test_phase2.csv"

df = pd.read_csv(DATA_FILE)

# Same environmental conditions for everyone.
sample = df.iloc[0].copy()

# Phase 2 prepared data contains temporal features but not timestamp.
sample["timestamp"] = "2026-09-13 20:00:00"


# ============================================================
# Create persona-specific interaction histories
# ============================================================

fitness_interactions = pd.DataFrame([
    {
        "user_id": "fitness_001",
        "card_id": "running_conditions",
        "action": "expand",
        "timestamp": "2026-09-12 09:00:00",
        "position": 1,
        "session_id": "fitness_session_1",
    },
    {
        "user_id": "fitness_001",
        "card_id": "running_conditions",
        "action": "click",
        "timestamp": "2026-09-12 09:05:00",
        "position": 1,
        "session_id": "fitness_session_1",
    },
    {
        "user_id": "fitness_001",
        "card_id": "running_conditions",
        "action": "expand",
        "timestamp": "2026-09-12 09:10:00",
        "position": 1,
        "session_id": "fitness_session_1",
    },
    {
        "user_id": "fitness_001",
        "card_id": "uv_allergy",
        "action": "expand",
        "timestamp": "2026-09-12 09:15:00",
        "position": 2,
        "session_id": "fitness_session_1",
    },
    {
        "user_id": "fitness_001",
        "card_id": "uv_allergy",
        "action": "click",
        "timestamp": "2026-09-12 09:20:00",
        "position": 2,
        "session_id": "fitness_session_1",
    },
])


farmer_interactions = pd.DataFrame([
    {
        "user_id": "farmer_001",
        "card_id": "farm_garden",
        "action": "expand",
        "timestamp": "2026-09-12 09:00:00",
        "position": 1,
        "session_id": "farmer_session_1",
    },
    {
        "user_id": "farmer_001",
        "card_id": "farm_garden",
        "action": "click",
        "timestamp": "2026-09-12 09:05:00",
        "position": 1,
        "session_id": "farmer_session_1",
    },
    {
        "user_id": "farmer_001",
        "card_id": "farm_garden",
        "action": "expand",
        "timestamp": "2026-09-12 09:10:00",
        "position": 1,
        "session_id": "farmer_session_1",
    },
    {
        "user_id": "farmer_001",
        "card_id": "rain_forecast",
        "action": "expand",
        "timestamp": "2026-09-12 09:15:00",
        "position": 2,
        "session_id": "farmer_session_1",
    },
    {
        "user_id": "farmer_001",
        "card_id": "rain_forecast",
        "action": "click",
        "timestamp": "2026-09-12 09:20:00",
        "position": 2,
        "session_id": "farmer_session_1",
    },
])


traveler_interactions = pd.DataFrame([
    {
        "user_id": "traveler_001",
        "card_id": "weather_conditions",
        "action": "expand",
        "timestamp": "2026-09-12 09:00:00",
        "position": 1,
        "session_id": "traveler_session_1",
    },
    {
        "user_id": "traveler_001",
        "card_id": "weather_conditions",
        "action": "click",
        "timestamp": "2026-09-12 09:05:00",
        "position": 1,
        "session_id": "traveler_session_1",
    },
    {
        "user_id": "traveler_001",
        "card_id": "rain_forecast",
        "action": "expand",
        "timestamp": "2026-09-12 09:10:00",
        "position": 2,
        "session_id": "traveler_session_1",
    },
    {
        "user_id": "traveler_001",
        "card_id": "rain_forecast",
        "action": "click",
        "timestamp": "2026-09-12 09:15:00",
        "position": 2,
        "session_id": "traveler_session_1",
    },
    {
        "user_id": "traveler_001",
        "card_id": "temperature",
        "action": "expand",
        "timestamp": "2026-09-12 09:20:00",
        "position": 3,
        "session_id": "traveler_session_1",
    },
])


# ============================================================
# Helper
# ============================================================

def test_persona(persona, interactions):

    ranking = get_personalized_ranking(
        sample,
        persona,
        interactions,
    )

    print("\n================================")
    print(f"{persona.upper()} USER")
    print("================================")

    print("City:", sample["city"])
    print("Interactions:", len(interactions))

    print("\nRanking:")

    for _, row in ranking.iterrows():
        print(
            f"{int(row['rank'])}. "
            f"{row['card']:20s} "
            f"ML={row['cold_start_score']:.4f} "
            f"behavior={row['preference_score']:.4f} "
            f"final={row['final_score']:.4f}"
        )

    return ranking


# ============================================================
# Run validation
# ============================================================

print("\n================================")
print("PHASE 2 PERSONA + BEHAVIOR VALIDATION")
print("================================")

print("\nSame environmental conditions")
print("Different personas and behavior")

fitness_ranking = test_persona(
    "fitness",
    fitness_interactions,
)

farmer_ranking = test_persona(
    "farmer",
    farmer_interactions,
)

traveler_ranking = test_persona(
    "traveler",
    traveler_interactions,
)


# ============================================================
# Assertions
# ============================================================

assert not fitness_ranking.empty
assert not farmer_ranking.empty
assert not traveler_ranking.empty

assert set(fitness_ranking["card"]).issubset({
    "temperature",
    "weather_conditions",
    "humidity",
    "rain_forecast",
    "wind",
    "air_quality",
    "uv_allergy",
    "running_conditions",
})

assert "running_conditions" in set(fitness_ranking["card"])
assert "farm_garden" in set(farmer_ranking["card"])
assert "travel_conditions" in set(traveler_ranking["card"])

fitness_running = fitness_ranking[
    fitness_ranking["card"] == "running_conditions"
].iloc[0]

farmer_farm = farmer_ranking[
    farmer_ranking["card"] == "farm_garden"
].iloc[0]

traveler_weather = traveler_ranking[
    traveler_ranking["card"] == "weather_conditions"
].iloc[0]

assert fitness_running["preference_score"] > 0.5
assert farmer_farm["preference_score"] > 0.5
assert traveler_weather["preference_score"] > 0.5

print("\n================================")
print("PERSONA + BEHAVIOR TEST PASSED")
print("================================")
