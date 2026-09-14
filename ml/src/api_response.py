import json

import pandas as pd
from src.prediction_service import get_personalized_ranking

# ============================================================
# Build backend-ready response
# ============================================================

def build_api_response(
    weather_data,
    personas,
    interactions
):
    """
    Convert the Phase 2 ML ranking into a clean
    JSON-compatible response for the backend.
    """

    if isinstance(personas, str):
        personas = [personas]

    ranking = get_personalized_ranking(
        weather_data,
        personas,
        interactions
    )

    cards = []

    for _, row in ranking.iterrows():

        cards.append({
            "rank": int(row["rank"]),
            "card": row["card"],
            "score": round(
                float(row["final_score"]),
                4
            ),
            "insight": row["insight"]
        })

    response = {
        "city": weather_data["city"],
        "personas": personas,
        "cards": cards
    }

    return response


# ============================================================
# Phase 2 test
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
        },
        {
            "user_id": "user_001",
            "card_id": "air_quality",
            "action": "expand",
            "timestamp": "2026-09-13 09:10:00",
            "position": 2,
            "session_id": "session_001"
        }
    ])

    response = build_api_response(
        weather_data,
        personas,
        interactions
    )

    print("\n================================")
    print("PHASE 2 API RESPONSE")
    print("================================")

    print(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False
        )
    )
