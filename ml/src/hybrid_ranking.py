import pandas as pd
import numpy as np
import joblib

from behavioral_preference import build_preference_profile


# ============================================================
# Configuration
# ============================================================

MODEL_FILE = "models/personalization_model.pkl"
DATA_FILE = "data/processed/test.csv"

MIN_BEHAVIOR_WEIGHT = 0.00
MAX_BEHAVIOR_WEIGHT = 0.80

BEHAVIOR_GROWTH_RATE = 0.08

CARDS = [
    "aqi",
    "uv",
    "temperature",
    "humidity",
    "rain",
    "wind",
    "soil_moisture",
    "weather_condition"
]


# ============================================================
# Load model
# ============================================================

model = joblib.load(MODEL_FILE)


# ============================================================
# Get cold-start scores
# ============================================================

def get_cold_start_scores(sample, persona):

    rows = []

    for card in CARDS:

        row = sample.copy()

        row["persona"] = persona
        row["card"] = card

        rows.append(row)

    input_df = pd.DataFrame(rows)

    scores = model.predict(input_df)

    scores = np.clip(scores, 0, 1)

    return pd.DataFrame({
        "card_id": CARDS,
        "cold_start_score": scores
    })


# ============================================================
# Combine cold-start + behavioral scores
# ============================================================

def calculate_behavior_weight(interaction_count):
    """
    Dynamically determine how much we should trust
    observed user behavior.

    Behavior starts with almost no influence for a new user
    and gradually increases as interaction history grows.

    The weight is capped at 0.80 so that cold-start/context
    relevance always retains some influence.
    """

    if interaction_count <= 0:
        return MIN_BEHAVIOR_WEIGHT

    weight = (
        MAX_BEHAVIOR_WEIGHT
        *
        (
            1
            - np.exp(
                -BEHAVIOR_GROWTH_RATE
                * interaction_count
            )
        )
    )

    return min(
        weight,
        MAX_BEHAVIOR_WEIGHT
    )

def get_hybrid_ranking(
    sample,
    persona,
    interactions
):

    cold_start = get_cold_start_scores(
        sample,
        persona
    )


    # --------------------------------------------------------
    # Behavioral profile
    # --------------------------------------------------------

    behavior = build_preference_profile(
        interactions
    )

    interaction_count = len(interactions)

    behavior_weight = calculate_behavior_weight(
        interaction_count
    )

    cold_start_weight = 1 - behavior_weight


    behavior = behavior[
        ["card_id", "preference_score"]
    ]


    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    ranking = cold_start.merge(
        behavior,
        on="card_id",
        how="left"
    )


    # Cards with no interaction history
    # receive a neutral behavioral score.

    ranking["preference_score"] = (
        ranking["preference_score"]
        .fillna(0.5)
    )


    # --------------------------------------------------------
    # Hybrid score
    # --------------------------------------------------------

    ranking["final_score"] = (
        cold_start_weight
        * ranking["cold_start_score"]
        +
        behavior_weight
        * ranking["preference_score"]
    )


    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    ranking = ranking.sort_values(
        "final_score",
        ascending=False
    ).reset_index(drop=True)

    ranking["cold_start_weight"] = cold_start_weight
    ranking["behavior_weight"] = behavior_weight


    return ranking


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv(DATA_FILE)

    sample = df.iloc[0].copy()

    persona = "fitness"


    # --------------------------------------------------------
    # Simulated user behavior
    # --------------------------------------------------------

    interactions = pd.DataFrame([

        {
            "user_id": "user_001",
            "card_id": "aqi",
            "action": "expand",
            "timestamp": "2026-08-31 09:30:00",
            "position": 2,
            "session_id": "session_001"
        },

        {
            "user_id": "user_001",
            "card_id": "aqi",
            "action": "click",
            "timestamp": "2026-08-31 09:40:00",
            "position": 1,
            "session_id": "session_001"
        },

        {
            "user_id": "user_001",
            "card_id": "aqi",
            "action": "expand",
            "timestamp": "2026-08-31 10:00:00",
            "position": 1,
            "session_id": "session_002"
        },

        {
            "user_id": "user_001",
            "card_id": "humidity",
            "action": "expand",
            "timestamp": "2026-08-31 09:45:00",
            "position": 1,
            "session_id": "session_001"
        },

        {
            "user_id": "user_001",
            "card_id": "wind",
            "action": "dismiss",
            "timestamp": "2026-08-31 09:50:00",
            "position": 4,
            "session_id": "session_001"
        }

    ])


    # --------------------------------------------------------
    # Get ranking
    # --------------------------------------------------------

    ranking = get_hybrid_ranking(
        sample,
        persona,
        interactions
    )


    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\n================================")
    print("HYBRID PERSONALIZATION")
    print("================================")

    print("Persona:", persona)
    print("City:", sample["city"])

    print("\nInteraction count:", len(interactions))

    behavior_weight = calculate_behavior_weight(
        len(interactions)
    )

    print(
        f"Cold-start weight: "
        f"{1 - behavior_weight:.3f}"
    )

    print(
        f"Behavior weight: "
        f"{behavior_weight:.3f}"
    )

    print("\nRanking:")

    for index, row in ranking.iterrows():

        print(
            f"{index + 1}. "
            f"{row['card_id']:20s} "
            f"cold={row['cold_start_score']:.4f} "
            f"behavior={row['preference_score']:.4f} "
            f"final={row['final_score']:.4f}"
        )