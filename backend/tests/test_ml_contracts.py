from app.core.enums import (
    CardType,
    UserPersonaType,
)
from app.ml.contracts import (
    ML_CARD_MAP,
    ML_CARD_REVERSE_MAP,
    ML_PERSONA_MAP,
)


def test_backend_personas_map_to_ml_personas():
    assert ML_PERSONA_MAP[UserPersonaType.FARMER] == "farmer"

    assert ML_PERSONA_MAP[UserPersonaType.TRAVELLER] == "traveler"

    assert ML_PERSONA_MAP[UserPersonaType.HEALTH] == "health_conscious"


def test_backend_rainfall_maps_to_ml_rain():
    assert ML_CARD_MAP[CardType.RAINFALL] == "rain_forecast"

def test_all_backend_cards_have_ml_mapping():
    assert set(ML_CARD_MAP.keys()) == set(CardType)

    assert len(ML_CARD_MAP) == 15
    assert len(ML_CARD_REVERSE_MAP) == 15


def test_phase2_specialized_card_mappings():
    assert (
        ML_CARD_MAP[
            CardType.RUNNING_CONDITIONS
        ]
        == "running_conditions"
    )

    assert (
        ML_CARD_MAP[
            CardType.SURF_CONDITIONS
        ]
        == "surf_conditions"
    )

    assert (
        ML_CARD_MAP[
            CardType.TIDE_WATER
        ]
        == "tide_water"
    )

    assert (
        ML_CARD_MAP[
            CardType.COMMUTE_CONDITIONS
        ]
        == "commute_conditions"
    )

    assert (
        ML_CARD_MAP[
            CardType.TRAVEL_CONDITIONS
        ]
        == "travel_conditions"
    )

    assert (
        ML_CARD_MAP[
            CardType.FAMILY_SCHOOL
        ]
        == "family_school"
    )

    assert (
        ML_CARD_MAP[
            CardType.EVENT_CONDITIONS
        ]
        == "event_conditions"
    )