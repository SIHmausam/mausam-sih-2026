from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from src.behavioral_preference import build_preference_profile
from src.card_insights import get_card_insight

# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_FILE = BASE_DIR / "models" / "personalization_model_phase2.pkl"

from src.phase2_config import PERSONAS, CARDS, ELIGIBILITY


# ============================================================
# Load model
# ============================================================

model = joblib.load(MODEL_FILE)


# ============================================================
# Cold-start prediction
# ============================================================

def get_cold_start_scores(weather_data, personas):

    # --------------------------------------------------------
    # Normalize personas to a list
    # --------------------------------------------------------

    if isinstance(personas, str):
        personas = [personas]

    invalid_personas = [
        persona for persona in personas
        if persona not in PERSONAS
    ]

    if invalid_personas:
        raise ValueError(
            f"Unsupported persona(s): {invalid_personas}"
        )

    if not personas:
        raise ValueError(
            "At least one persona must be selected."
        )


    # --------------------------------------------------------
    # Build personalized candidate pool
    #
    # Eligibility controls ML personalization only.
    # It does NOT restrict the user's access to other cards.
    # --------------------------------------------------------

    eligible_cards = [
        card
        for card in CARDS
        if any(
            persona in ELIGIBILITY[card]
            for persona in personas
        )
    ]


    # --------------------------------------------------------
    # Marine-data gating
    #
    # Surfer cards require actual marine data.
    # --------------------------------------------------------

    marine_available = bool(
        weather_data.get(
            "marine_data_available",
            False
        )
    )

    if not marine_available:
        eligible_cards = [
            card
            for card in eligible_cards
            if card not in {
                "surf_conditions",
                "tide_water"
            }
        ]


    # --------------------------------------------------------
    # Predict each eligible card for each selected persona.
    #
    # The model was trained on individual persona + card
    # combinations, so multi-persona requests are evaluated
    # without inventing a new combined persona.
    # --------------------------------------------------------

    rows = []

    for persona in personas:

        for card in eligible_cards:

            row = weather_data.copy()

            row["persona"] = persona
            row["card"] = card

            rows.append(row)


    input_df = pd.DataFrame(rows)


    # --------------------------------------------------------
    # Temporal features required by the Phase 2 model
    #
    # Phase 2 preprocessing already provides these features.
    # --------------------------------------------------------

    required_time_features = [
        "hour",
        "day_of_week",
        "month",
    ]

    missing_time_features = [
        feature
        for feature in required_time_features
        if feature not in input_df.columns
    ]

    if missing_time_features:
        raise ValueError(
            "Missing Phase 2 temporal feature(s): "
            f"{missing_time_features}"
        )


    # --------------------------------------------------------
    # Model prediction
    # --------------------------------------------------------

    scores = model.predict(input_df)

    scores = np.clip(
        scores,
        0,
        1
    )


    predictions = pd.DataFrame({
        "persona": input_df["persona"].values,
        "card": input_df["card"].values,
        "cold_start_score": scores
    })


    # --------------------------------------------------------
    # Collapse multi-persona predictions.
    #
    # A card gets the strongest relevance score among the
    # selected personas that make it eligible.
    # --------------------------------------------------------

    predictions = (
        predictions
        .groupby("card", as_index=False)
        ["cold_start_score"]
        .max()
    )


    return predictions


# ============================================================
# Final personalized ranking
# ============================================================

def get_personalized_ranking(
    weather_data,
    personas,
    interactions
):

    # ========================================================
    # Phase 2 cold-start / ML relevance
    # ========================================================

    cold_start = get_cold_start_scores(
        weather_data,
        personas
    )


    # ========================================================
    # Behavioral preference
    #
    # behavioral_preference.py already applies:
    # - action weights
    # - position factor
    # - 7-day recency half-life
    # - per-card aggregation
    # - neutral 0.5 for insufficient evidence
    # ========================================================

    behavior = build_preference_profile(
        interactions,
        reference_time=weather_data["timestamp"]
        if "timestamp" in weather_data
        else pd.Timestamp.now()
    )

    if not behavior.empty:

        behavior = behavior[
            ["card_id", "preference_score"]
        ]

        behavior = behavior.rename(
            columns={
                "card_id": "card"
            }
        )

    else:

        behavior = pd.DataFrame(
            columns=[
                "card",
                "preference_score"
            ]
        )


    # ========================================================
    # Merge ML relevance with behavioral preference
    # ========================================================

    ranking = cold_start.merge(
        behavior,
        on="card",
        how="left"
    )


    # No history / no evidence = neutral behavior

    ranking["preference_score"] = (
        ranking["preference_score"]
        .fillna(0.5)
    )


    # ========================================================
    # Phase 2 final score
    #
    # Environmental/persona relevance remains dominant.
    # Behavior provides personalization without overpowering
    # current weather conditions.
    # ========================================================

    ML_WEIGHT = 0.75
    BEHAVIOR_WEIGHT = 0.25

    ranking["final_score"] = (
        ML_WEIGHT
        * ranking["cold_start_score"]
        +
        BEHAVIOR_WEIGHT
        * ranking["preference_score"]
    )


    # ========================================================
    # Rank
    # ========================================================

    ranking = ranking.sort_values(
        "final_score",
        ascending=False
    ).reset_index(drop=True)

    ranking["rank"] = (
        ranking.index + 1
    )

    ranking["ml_weight"] = ML_WEIGHT
    ranking["behavior_weight"] = BEHAVIOR_WEIGHT


    # ========================================================
    # Contextual insight for every personalized card
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
            "ml_weight",
            "behavior_weight",
            "insight"
        ]
    ]


# ============================================================
# Phase 2 smoke test
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv(
        "data/processed/test_phase2.csv"
    )

    weather_data = df.iloc[0].copy()

    personas = [
        "farmer",
        "health_conscious"
    ]

    interactions = pd.DataFrame([
        {
            "user_id": "user_001",
            "card_id": "farm_garden",
            "action": "expand",
            "timestamp": "2026-09-13 09:00:00",
            "position": 1,
            "session_id": "session_001"
        },
        {
            "user_id": "user_001",
            "card_id": "farm_garden",
            "action": "click",
            "timestamp": "2026-09-13 09:05:00",
            "position": 1,
            "session_id": "session_001"
        }
    ])


    result = get_personalized_ranking(
        weather_data,
        personas,
        interactions
    )


    print("\n================================")
    print("PHASE 2 ML PREDICTION SERVICE")
    print("================================")

    print(
        "City:",
        weather_data["city"]
    )

    print(
        "Personas:",
        personas
    )

    print(
        "Personalized cards:",
        len(result)
    )

    print("\nRanking:")

    print(
        result[
            [
                "rank",
                "card",
                "final_score",
                "cold_start_score",
                "preference_score",
                "insight"
            ]
        ].to_string(index=False)
    )
