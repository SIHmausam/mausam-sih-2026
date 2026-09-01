from app.core.enums import (
    CardType,
    UserPersonaType,
)
from app.ml.contracts import (
    ML_CARD_MAP,
    ML_PERSONA_MAP,
)


def test_backend_personas_map_to_ml_personas():
    assert ML_PERSONA_MAP[UserPersonaType.FARMER] == "farmer"

    assert ML_PERSONA_MAP[UserPersonaType.TRAVELLER] == "traveler"

    assert ML_PERSONA_MAP[UserPersonaType.HEALTH] == "fitness"


def test_backend_rainfall_maps_to_ml_rain():
    assert ML_CARD_MAP[CardType.RAINFALL] == "rain"
