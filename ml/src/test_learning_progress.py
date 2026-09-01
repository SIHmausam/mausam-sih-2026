import numpy as np


# ============================================================
# Configuration
# ============================================================

MAX_BEHAVIOR_WEIGHT = 0.80
BEHAVIOR_GROWTH_RATE = 0.08


# ============================================================
# Dynamic behavior weight
# ============================================================

def calculate_behavior_weight(interaction_count):

    if interaction_count <= 0:
        return 0.0

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


# ============================================================
# Test learning progression
# ============================================================

if __name__ == "__main__":

    interaction_counts = [
        0,
        5,
        10,
        20,
        50,
        100
    ]

    print("\n================================")
    print("PERSONALIZATION LEARNING")
    print("================================")

    print(
        f"{'Interactions':<15}"
        f"{'Cold-start':<15}"
        f"{'Behavior':<15}"
    )

    print("-" * 45)

    for count in interaction_counts:

        behavior_weight = calculate_behavior_weight(
            count
        )

        cold_start_weight = (
            1 - behavior_weight
        )

        print(
            f"{count:<15}"
            f"{cold_start_weight:<15.3f}"
            f"{behavior_weight:<15.3f}"
        )