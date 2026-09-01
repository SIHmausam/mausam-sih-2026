import pandas as pd

from behavioral_preference import build_preference_profile
from hybrid_ranking import get_hybrid_ranking


# ============================================================
# Load weather data
# ============================================================

DATA_FILE = "data/processed/test.csv"

df = pd.read_csv(DATA_FILE)

sample = df.iloc[0].copy()

persona = "fitness"


# ============================================================
# Helper function
# ============================================================

def show_ranking(session_name, interactions):

    ranking = get_hybrid_ranking(
        sample,
        persona,
        interactions
    )

    print("\n================================")
    print(session_name)
    print("================================")

    print(
        "Total interactions:",
        len(interactions)
    )

    print("\nTop ranking:")

    for index, row in ranking.iterrows():

        print(
            f"{index + 1}. "
            f"{row['card_id']:20s} "
            f"final={row['final_score']:.4f}"
        )

    return ranking


# ============================================================
# SESSION 1
# ============================================================

session_1 = pd.DataFrame([

    {
        "user_id": "user_001",
        "card_id": "aqi",
        "action": "expand",
        "timestamp": "2026-08-31 09:00:00",
        "position": 1,
        "session_id": "session_001"
    },

    {
        "user_id": "user_001",
        "card_id": "aqi",
        "action": "click",
        "timestamp": "2026-08-31 09:05:00",
        "position": 1,
        "session_id": "session_001"
    },

    {
        "user_id": "user_001",
        "card_id": "humidity",
        "action": "expand",
        "timestamp": "2026-08-31 09:10:00",
        "position": 2,
        "session_id": "session_001"
    }

])


show_ranking(
    "SESSION 1",
    session_1
)


# ============================================================
# SESSION 2
# ============================================================

session_2 = pd.DataFrame([

    {
        "user_id": "user_001",
        "card_id": "aqi",
        "action": "expand",
        "timestamp": "2026-08-31 15:00:00",
        "position": 1,
        "session_id": "session_002"
    },

    {
        "user_id": "user_001",
        "card_id": "aqi",
        "action": "click",
        "timestamp": "2026-08-31 15:05:00",
        "position": 1,
        "session_id": "session_002"
    },

    {
        "user_id": "user_001",
        "card_id": "uv",
        "action": "expand",
        "timestamp": "2026-08-31 15:10:00",
        "position": 2,
        "session_id": "session_002"
    }

])


# IMPORTANT:
# Combine old + new interactions.
all_sessions = pd.concat(
    [session_1, session_2],
    ignore_index=True
)


show_ranking(
    "SESSION 2 — WITH PREVIOUS HISTORY",
    all_sessions
)


# ============================================================
# SESSION 3
# ============================================================

session_3 = pd.DataFrame([

    {
        "user_id": "user_001",
        "card_id": "uv",
        "action": "expand",
        "timestamp": "2026-08-31 20:00:00",
        "position": 2,
        "session_id": "session_003"
    },

    {
        "user_id": "user_001",
        "card_id": "uv",
        "action": "click",
        "timestamp": "2026-08-31 20:05:00",
        "position": 1,
        "session_id": "session_003"
    },

    {
        "user_id": "user_001",
        "card_id": "aqi",
        "action": "view",
        "timestamp": "2026-08-31 20:10:00",
        "position": 1,
        "session_id": "session_003"
    }

])


all_sessions = pd.concat(
    [
        session_1,
        session_2,
        session_3
    ],
    ignore_index=True
)


show_ranking(
    "SESSION 3 — CUMULATIVE HISTORY",
    all_sessions
)


# ============================================================
# Preference profile
# ============================================================

profile = build_preference_profile(
    all_sessions
)


print("\n================================")
print("FINAL USER PREFERENCE PROFILE")
print("================================")

print(
    profile.to_string(
        index=False
    )
)