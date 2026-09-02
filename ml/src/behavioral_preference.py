import pandas as pd
import numpy as np


# ============================================================
# Configuration
# ============================================================

ACTION_WEIGHTS = {
    "view": 0.05,
    "click": 0.15,
    "expand": 0.25,
    "dismiss": -0.20
}

MAX_POSITION_BONUS = 1.0


# ============================================================
# Position bias adjustment
# ============================================================

def position_factor(position):
    """
    Reduce the strength of an interaction when a card
    appeared lower on the homepage.

    Backend position 1 = first card
    Backend position 2 = second card
    etc.
    """

    position = max(int(position) - 1, 0)

    return 1 / (1 + 0.15 * position)


# ============================================================
# Calculate interaction strength
# ============================================================

def calculate_interaction_score(row):
    """
    Calculate the preference contribution of one interaction.
    """

    action = row["action"]

    if action not in ACTION_WEIGHTS:
        return 0.0

    base_weight = ACTION_WEIGHTS[action]

    position_multiplier = position_factor(
        row["position"]
    )

    return base_weight * position_multiplier


# ============================================================
# Calculate recency weight
# ============================================================

def calculate_recency_weight(timestamp, reference_time):
    """
    Recent interactions have greater influence.

    Half-life = 7 days.
    """

    timestamp = pd.to_datetime(timestamp)
    reference_time = pd.to_datetime(reference_time)

    age_days = max(
        (reference_time - timestamp).total_seconds() / 86400,
        0
    )

    return np.exp(
        -np.log(2) * age_days / 7
    )


# ============================================================
# Build user preference profile
# ============================================================

def build_preference_profile(interactions, reference_time):
    """
    Convert raw interactions into stable 0–1 preference scores.

    0.0 = strong negative preference
    0.5 = neutral / insufficient evidence
    1.0 = strong positive preference

    The score is calculated independently for each card,
    so one card's behavior does not change another card's score.
    """

    if interactions.empty:
        return pd.DataFrame(
            columns=[
                "card_id",
                "raw_score",
                "interaction_count",
                "preference_score"
            ]
        )

    interactions = interactions.copy()

    interactions["timestamp"] = pd.to_datetime(
        interactions["timestamp"]
    )

    # --------------------------------------------------------
    # Interaction score
    # --------------------------------------------------------

    interactions["interaction_score"] = (
        interactions.apply(
            calculate_interaction_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

    interactions["recency_weight"] = (
        interactions["timestamp"]
        .apply(
            lambda timestamp:
            calculate_recency_weight(
                timestamp,
                reference_time
            )
        )
    )

    # --------------------------------------------------------
    # Weighted contribution
    # --------------------------------------------------------

    interactions["weighted_score"] = (
        interactions["interaction_score"]
        *
        interactions["recency_weight"]
    )

    # --------------------------------------------------------
    # Aggregate independently for each card
    # --------------------------------------------------------

    profile = (
        interactions
        .groupby("card_id")
        .agg(
            raw_score=(
                "weighted_score",
                "sum"
            ),
            interaction_count=(
                "card_id",
                "count"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Stable preference transformation
    # --------------------------------------------------------
    #
    # Start from neutral = 0.5.
    #
    # Positive evidence pushes toward 1.
    # Negative evidence pushes toward 0.
    #
    # tanh prevents unlimited growth from repeated clicks.
    # --------------------------------------------------------

    profile["preference_score"] = (
        0.5
        +
        0.5
        *
        np.tanh(
            profile["raw_score"]
        )
    )

    # Keep score safely inside 0–1.

    profile["preference_score"] = (
        profile["preference_score"]
        .clip(0, 1)
    )

    return profile.sort_values(
        "preference_score",
        ascending=False
    ).reset_index(drop=True)


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

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
            "card_id": "uv",
            "action": "view",
            "timestamp": "2026-08-31 09:42:00",
            "position": 3,
            "session_id": "session_001"
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
        },

        {
            "user_id": "user_001",
            "card_id": "aqi",
            "action": "expand",
            "timestamp": "2026-08-31 10:00:00",
            "position": 1,
            "session_id": "session_002"
        }

    ])


    profile = build_preference_profile(
        interactions
    )


    print("\n================================")
    print("BEHAVIORAL PREFERENCE PROFILE")
    print("================================")

    print(profile.to_string(index=False))