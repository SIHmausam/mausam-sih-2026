import pandas as pd

from hybrid_ranking import get_hybrid_ranking


# ============================================================
# Load current conditions
# ============================================================

DATA_FILE = "data/processed/test.csv"

df = pd.read_csv(DATA_FILE)

# Same environmental conditions for everyone
sample = df.iloc[0].copy()


# ============================================================
# Create persona-specific interaction histories
# ============================================================

fitness_interactions = pd.DataFrame([

    {
        "user_id": "fitness_001",
        "card_id": "aqi",
        "action": "expand",
        "timestamp": "2026-08-31 09:00:00",
        "position": 1,
        "session_id": "fitness_session_1"
    },
    {
        "user_id": "fitness_001",
        "card_id": "aqi",
        "action": "click",
        "timestamp": "2026-08-31 09:05:00",
        "position": 1,
        "session_id": "fitness_session_1"
    },
    {
        "user_id": "fitness_001",
        "card_id": "aqi",
        "action": "expand",
        "timestamp": "2026-08-31 09:10:00",
        "position": 1,
        "session_id": "fitness_session_1"
    },
    {
        "user_id": "fitness_001",
        "card_id": "uv",
        "action": "expand",
        "timestamp": "2026-08-31 09:15:00",
        "position": 2,
        "session_id": "fitness_session_1"
    },
    {
        "user_id": "fitness_001",
        "card_id": "uv",
        "action": "click",
        "timestamp": "2026-08-31 09:20:00",
        "position": 2,
        "session_id": "fitness_session_1"
    }

])


farmer_interactions = pd.DataFrame([

    {
        "user_id": "farmer_001",
        "card_id": "soil_moisture",
        "action": "expand",
        "timestamp": "2026-08-31 09:00:00",
        "position": 1,
        "session_id": "farmer_session_1"
    },
    {
        "user_id": "farmer_001",
        "card_id": "soil_moisture",
        "action": "click",
        "timestamp": "2026-08-31 09:05:00",
        "position": 1,
        "session_id": "farmer_session_1"
    },
    {
        "user_id": "farmer_001",
        "card_id": "soil_moisture",
        "action": "expand",
        "timestamp": "2026-08-31 09:10:00",
        "position": 1,
        "session_id": "farmer_session_1"
    },
    {
        "user_id": "farmer_001",
        "card_id": "rain",
        "action": "expand",
        "timestamp": "2026-08-31 09:15:00",
        "position": 2,
        "session_id": "farmer_session_1"
    },
    {
        "user_id": "farmer_001",
        "card_id": "rain",
        "action": "click",
        "timestamp": "2026-08-31 09:20:00",
        "position": 2,
        "session_id": "farmer_session_1"
    }

])


traveler_interactions = pd.DataFrame([

    {
        "user_id": "traveler_001",
        "card_id": "weather_condition",
        "action": "expand",
        "timestamp": "2026-08-31 09:00:00",
        "position": 1,
        "session_id": "traveler_session_1"
    },
    {
        "user_id": "traveler_001",
        "card_id": "weather_condition",
        "action": "click",
        "timestamp": "2026-08-31 09:05:00",
        "position": 1,
        "session_id": "traveler_session_1"
    },
    {
        "user_id": "traveler_001",
        "card_id": "rain",
        "action": "expand",
        "timestamp": "2026-08-31 09:10:00",
        "position": 2,
        "session_id": "traveler_session_1"
    },
    {
        "user_id": "traveler_001",
        "card_id": "rain",
        "action": "click",
        "timestamp": "2026-08-31 09:15:00",
        "position": 2,
        "session_id": "traveler_session_1"
    },
    {
        "user_id": "traveler_001",
        "card_id": "temperature",
        "action": "expand",
        "timestamp": "2026-08-31 09:20:00",
        "position": 3,
        "session_id": "traveler_session_1"
    }

])


# ============================================================
# Helper
# ============================================================

def test_persona(
    persona,
    interactions
):

    ranking = get_hybrid_ranking(
        sample,
        persona,
        interactions
    )

    print("\n================================")
    print(f"{persona.upper()} USER")
    print("================================")

    print(
        "City:",
        sample["city"]
    )

    print(
        "Interactions:",
        len(interactions)
    )

    print("\nRanking:")

    for index, row in ranking.iterrows():

        print(
            f"{index + 1}. "
            f"{row['card_id']:20s} "
            f"final={row['final_score']:.4f}"
        )


# ============================================================
# Run tests
# ============================================================

print("\n================================")
print("PERSONA + BEHAVIOR VALIDATION")
print("================================")

print("\nSame environmental conditions")
print("Different personas and behavior")

test_persona(
    "fitness",
    fitness_interactions
)

test_persona(
    "farmer",
    farmer_interactions
)

test_persona(
    "traveler",
    traveler_interactions
)