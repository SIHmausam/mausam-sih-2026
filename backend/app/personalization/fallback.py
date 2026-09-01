from app.core.enums import (
    CardType,
    UserPersonaType,
)
from app.schemas.personalization import (
    PersonalizedCard,
)

FALLBACK_CARD_ORDER: dict[
    UserPersonaType,
    tuple[CardType, ...],
] = {
    UserPersonaType.HEALTH: (
        CardType.AQI,
        CardType.UV,
        CardType.TEMPERATURE,
        CardType.HUMIDITY,
        CardType.WEATHER_CONDITION,
        CardType.RAINFALL,
        CardType.WIND,
        CardType.SOIL_MOISTURE,
    ),
    UserPersonaType.FARMER: (
        CardType.RAINFALL,
        CardType.SOIL_MOISTURE,
        CardType.HUMIDITY,
        CardType.WEATHER_CONDITION,
        CardType.WIND,
        CardType.TEMPERATURE,
        CardType.UV,
        CardType.AQI,
    ),
    UserPersonaType.TRAVELLER: (
        CardType.WEATHER_CONDITION,
        CardType.RAINFALL,
        CardType.TEMPERATURE,
        CardType.WIND,
        CardType.AQI,
        CardType.HUMIDITY,
        CardType.UV,
        CardType.SOIL_MOISTURE,
    ),
}


def build_fallback_ranking(
    persona: UserPersonaType,
) -> list[PersonalizedCard]:
    order = FALLBACK_CARD_ORDER[persona]

    return [
        PersonalizedCard(
            rank=index,
            card=card,
            score=None,
            insight=None,
        )
        for index, card in enumerate(
            order,
            start=1,
        )
    ]
