"""
Mausam Personalization - User Interaction Schema

This file defines the structure of user interaction
data that will later be collected by the application.
"""

INTERACTION_FIELDS = {
    "user_id": "Unique identifier for the user",
    "card_id": "Information card interacted with",
    "action": "view / click / expand / dismiss",
    "timestamp": "Time of interaction",
    "position": "Position of the card when displayed",
    "session_id": "Identifier for the current app session"
}


VALID_ACTIONS = {
    "view",
    "click",
    "expand",
    "dismiss"
}


def validate_interaction(interaction):
    """
    Validate a single interaction record.
    """

    required_fields = INTERACTION_FIELDS.keys()

    # Check required fields
    for field in required_fields:
        if field not in interaction:
            return False, f"Missing field: {field}"

    # Check action
    if interaction["action"] not in VALID_ACTIONS:
        return False, "Invalid action"

    # Check position
    if not isinstance(interaction["position"], int):
        return False, "Position must be an integer"

    if interaction["position"] < 1:
        return False, "Position must be >= 1"

    return True, "Valid interaction"


if __name__ == "__main__":

    example_interaction = {
        "user_id": "user_001",
        "card_id": "uv_index",
        "action": "expand",
        "timestamp": "2026-08-31 10:32:00",
        "position": 2,
        "session_id": "session_123"
    }

    valid, message = validate_interaction(
        example_interaction
    )

    print("Interaction:")
    print(example_interaction)

    print("\nValidation:")
    print(valid, "-", message)