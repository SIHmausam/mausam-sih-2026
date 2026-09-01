import os
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INTERACTION_FILE = "data/user_interactions.csv"

COLUMNS = [
    "user_id",
    "card_id",
    "action",
    "timestamp",
    "position",
    "session_id"
]


# ============================================================
# Initialize interaction store
# ============================================================

def initialize_store():

    os.makedirs(
        os.path.dirname(INTERACTION_FILE),
        exist_ok=True
    )

    if (
        not os.path.exists(INTERACTION_FILE)
        or os.path.getsize(INTERACTION_FILE) == 0
    ):
        pd.DataFrame(
            columns=COLUMNS
        ).to_csv(
            INTERACTION_FILE,
            index=False
        )


# ============================================================
# Save interaction
# ============================================================

def save_interaction(interaction):

    initialize_store()

    df = pd.DataFrame(
        [interaction],
        columns=COLUMNS
    )

    df.to_csv(
        INTERACTION_FILE,
        mode="a",
        header=False,
        index=False
    )


# ============================================================
# Load user history
# ============================================================

def get_user_interactions(user_id):

    initialize_store()

    df = pd.read_csv(
        INTERACTION_FILE
    )

    if df.empty:
        return df

    return df[
        df["user_id"] == user_id
    ].copy()


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    test_interaction = {
        "user_id": "user_001",
        "card_id": "aqi",
        "action": "expand",
        "timestamp": "2026-08-31 23:45:00",
        "position": 2,
        "session_id": "session_001"
    }

    save_interaction(
        test_interaction
    )

    history = get_user_interactions(
        "user_001"
    )

    print("\n================================")
    print("INTERACTION STORE TEST")
    print("================================")

    print("\nSaved interaction:")
    print(test_interaction)

    print("\nUser history:")
    print(history.to_string(index=False))