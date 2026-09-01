import json
import pandas as pd

from src.prediction_service import get_personalized_ranking


# ============================================================
# Build backend-ready response
# ============================================================

def build_api_response(
    weather_data,
    persona,
    interactions
):
    """
    Convert the ML ranking into a clean JSON-compatible
    response for the backend.
    """

    ranking = get_personalized_ranking(
        weather_data,
        persona,
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
        "persona": persona,
        "cards": cards
    }

    return response


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv(
        "data/processed/test.csv"
    )

    weather_data = df.iloc[0].copy()

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

    response = build_api_response(
        weather_data,
        persona,
        interactions
    )

    print("\n================================")
    print("API RESPONSE")
    print("================================")

    print(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False
        )
    )