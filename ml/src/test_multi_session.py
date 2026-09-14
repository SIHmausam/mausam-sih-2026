import pandas as pd

from src.behavioral_preference import build_preference_profile
from src.prediction_service import get_personalized_ranking


# ============================================================
# Load Phase 2 weather data
# ============================================================

DATA_FILE = "data/processed/test_phase2.csv"

df = pd.read_csv(DATA_FILE)

sample = df.iloc[0].copy()

# test_phase2.csv contains temporal features but not timestamp.
# Use an explicit API-style timestamp for the ranking reference.
sample["timestamp"] = "2026-09-13 20:00:00"


personas = [
    "fitness"
]


# ============================================================
# Helper
# ============================================================

def show_ranking(session_name, interactions):

    ranking = get_personalized_ranking(
        sample,
        personas,
        interactions
    )

    print("\n================================")
    print(session_name)
    print("================================")

    print(
        "Total interactions:",
        len(interactions)
    )

    print("\nRanking:")

    for _, row in ranking.iterrows():

        print(
            f"{row['rank']}. "
            f"{row['card']:20s} "
            f"ML={row['cold_start_score']:.4f} "
            f"behavior={row['preference_score']:.4f} "
            f"final={row['final_score']:.4f}"
        )

    return ranking


# ============================================================
# SESSION 1
# ============================================================

session_1 = pd.DataFrame([

    {
        "user_id": "user_001",
        "card_id": "running_conditions",
        "action": "expand",
        "timestamp": "2026-09-13 09:00:00",
        "position": 1,
        "session_id": "session_001"
    },

    {
        "user_id": "user_001",
        "card_id": "running_conditions",
        "action": "click",
        "timestamp": "2026-09-13 09:05:00",
        "position": 1,
        "session_id": "session_001"
    },

    {
        "user_id": "user_001",
        "card_id": "wind",
        "action": "expand",
        "timestamp": "2026-09-13 09:10:00",
        "position": 2,
        "session_id": "session_001"
    }

])


ranking_1 = show_ranking(
    "SESSION 1",
    session_1
)


# ============================================================
# SESSION 2
# ============================================================

session_2 = pd.DataFrame([

    {
        "user_id": "user_001",
        "card_id": "running_conditions",
        "action": "expand",
        "timestamp": "2026-09-13 15:00:00",
        "position": 1,
        "session_id": "session_002"
    },

    {
        "user_id": "user_001",
        "card_id": "running_conditions",
        "action": "click",
        "timestamp": "2026-09-13 15:05:00",
        "position": 1,
        "session_id": "session_002"
    },

    {
        "user_id": "user_001",
        "card_id": "uv_allergy",
        "action": "expand",
        "timestamp": "2026-09-13 15:10:00",
        "position": 2,
        "session_id": "session_002"
    }

])


all_sessions_2 = pd.concat(
    [
        session_1,
        session_2
    ],
    ignore_index=True
)


ranking_2 = show_ranking(
    "SESSION 2 — WITH PREVIOUS HISTORY",
    all_sessions_2
)


# ============================================================
# SESSION 3
# ============================================================

session_3 = pd.DataFrame([

    {
        "user_id": "user_001",
        "card_id": "running_conditions",
        "action": "expand",
        "timestamp": "2026-09-13 20:00:00",
        "position": 1,
        "session_id": "session_003"
    },

    {
        "user_id": "user_001",
        "card_id": "running_conditions",
        "action": "click",
        "timestamp": "2026-09-13 20:05:00",
        "position": 1,
        "session_id": "session_003"
    },

    {
        "user_id": "user_001",
        "card_id": "wind",
        "action": "view",
        "timestamp": "2026-09-13 20:10:00",
        "position": 1,
        "session_id": "session_003"
    }

])


all_sessions_3 = pd.concat(
    [
        session_1,
        session_2,
        session_3
    ],
    ignore_index=True
)


ranking_3 = show_ranking(
    "SESSION 3 — CUMULATIVE HISTORY",
    all_sessions_3
)


# ============================================================
# Behavioral preference profile
# ============================================================

profile = build_preference_profile(
    all_sessions_3,
    reference_time=sample["timestamp"]
)


print("\n================================")
print("FINAL USER PREFERENCE PROFILE")
print("================================")

print(
    profile.to_string(
        index=False
    )
)


# ============================================================
# Behavioral validation
# ============================================================

running_preference = profile.loc[
    profile["card_id"] == "running_conditions",
    "preference_score"
].iloc[0]

wind_preference = profile.loc[
    profile["card_id"] == "wind",
    "preference_score"
].iloc[0]


assert running_preference > 0.5
assert wind_preference > 0.5

print("\n================================")
print("MULTI-SESSION BEHAVIOR TEST PASSED")
print("================================")
