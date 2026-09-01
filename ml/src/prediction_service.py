import pandas as pd
import numpy as np
import joblib

from src.behavioral_preference import build_preference_profile
from src.card_insights import get_card_insight

# ============================================================
# Configuration
# ============================================================

MODEL_FILE = "models/personalization_model.pkl"

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
# Cold-start prediction
# ============================================================

def get_cold_start_scores(weather_data, persona):

    rows = []

    for card in CARDS:

        row = weather_data.copy()

        row["persona"] = persona
        row["card"] = card

        rows.append(row)

    input_df = pd.DataFrame(rows)

    # ========================================================
    # Add time features required by the trained model
    # ========================================================

    timestamp = pd.to_datetime(
        input_df["timestamp"]
    )

    input_df["hour"] = timestamp.dt.hour
    input_df["day_of_week"] = timestamp.dt.dayofweek
    input_df["month"] = timestamp.dt.month

    # ========================================================
    # Generate predictions
    # ========================================================

    scores = model.predict(input_df)

    scores = np.clip(scores, 0, 1)

    return pd.DataFrame({
        "card": CARDS,
        "cold_start_score": scores
    })


# ============================================================
# Final personalized ranking
# ============================================================

def get_personalized_ranking(
    weather_data,
    persona,
    interactions
):

    cold_start = get_cold_start_scores(
        weather_data,
        persona
    )

    interaction_count = len(interactions)

    # --------------------------------------------------------
    # Dynamic behavior weight
    # --------------------------------------------------------

    if interaction_count <= 0:

        behavior_weight = 0.0

    else:

        behavior_weight = (
            0.80
            *
            (
                1
                -
                np.exp(
                    -0.08 * interaction_count
                )
            )
        )

        behavior_weight = min(
            behavior_weight,
            0.80
        )

    cold_start_weight = (
        1 - behavior_weight
    )


    # --------------------------------------------------------
    # Behavioral preference
    # --------------------------------------------------------

    behavior = build_preference_profile(
        interactions
    )

    behavior = behavior[
        ["card_id", "preference_score"]
    ]

    behavior = behavior.rename(
        columns={
            "card_id": "card"
        }
    )


    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    ranking = cold_start.merge(
        behavior,
        on="card",
        how="left"
    )


    # No history = neutral behavior

    ranking["preference_score"] = (
        ranking["preference_score"]
        .fillna(0.5)
    )


    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    ranking["final_score"] = (
        cold_start_weight
        * ranking["cold_start_score"]
        +
        behavior_weight
        * ranking["preference_score"]
    )


    # --------------------------------------------------------
    # Ranking
    # --------------------------------------------------------

    ranking = ranking.sort_values(
        "final_score",
        ascending=False
    ).reset_index(drop=True)


    ranking["rank"] = (
        ranking.index + 1
    )

    ranking["cold_start_weight"] = (
        cold_start_weight
    )

    ranking["behavior_weight"] = (
        behavior_weight
    )


    # ========================================================
    # Add contextual insight for every card
    # ========================================================

    ranking["insight"] = ranking["card"].apply(
        lambda card: get_card_insight(
            card,
            weather_data
        )
    )


    return ranking[
        [
            "rank",
            "card",
            "final_score",
            "cold_start_score",
            "preference_score",
            "cold_start_weight",
            "behavior_weight",
            "insight"
        ]
    ]


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Example weather record
    # --------------------------------------------------------

    df = pd.read_csv(
        "data/processed/test.csv"
    )

    weather_data = df.iloc[0].copy()


    # --------------------------------------------------------
    # Example user
    # --------------------------------------------------------

    persona = "farmer"


    interactions = pd.DataFrame([
        {
            "user_id": "user_001",
            "card_id": "soil_moisture",
            "action": "expand",
            "timestamp": "2026-08-31 09:00:00",
            "position": 1,
            "session_id": "session_001"
        },
        {
            "user_id": "user_001",
            "card_id": "soil_moisture",
            "action": "click",
            "timestamp": "2026-08-31 09:05:00",
            "position": 1,
            "session_id": "session_001"
        },
        {
            "user_id": "user_001",
            "card_id": "rain",
            "action": "expand",
            "timestamp": "2026-08-31 09:10:00",
            "position": 2,
            "session_id": "session_001"
        }
    ])


    # --------------------------------------------------------
    # Generate ranking
    # --------------------------------------------------------

    result = get_personalized_ranking(
        weather_data,
        persona,
        interactions
    )


    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\n================================")
    print("ML PREDICTION SERVICE")
    print("================================")

    print(
        "City:",
        weather_data["city"]
    )

    print(
        "Persona:",
        persona
    )

    print(
        "Interactions:",
        len(interactions)
    )

    print("\nRanking:")

    print(
        result.to_string(
            index=False
        )
    )