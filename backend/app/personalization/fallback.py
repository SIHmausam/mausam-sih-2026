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
    ),

    UserPersonaType.FITNESS: (
        CardType.RUNNING_CONDITIONS,
        CardType.TEMPERATURE,
        CardType.AQI,
        CardType.UV,
        CardType.WEATHER_CONDITION,
        CardType.RAINFALL,
        CardType.WIND,
        CardType.HUMIDITY,
    ),

    UserPersonaType.SURFER: (
        CardType.SURF_CONDITIONS,
        CardType.TIDE_WATER,
        CardType.WIND,
        CardType.WEATHER_CONDITION,
        CardType.RAINFALL,
        CardType.TEMPERATURE,
        CardType.UV,
        CardType.HUMIDITY,
        CardType.AQI,
    ),

    UserPersonaType.TRAVELLER: (
        CardType.TRAVEL_CONDITIONS,
        CardType.COMMUTE_CONDITIONS,
        CardType.WEATHER_CONDITION,
        CardType.RAINFALL,
        CardType.TEMPERATURE,
        CardType.WIND,
        CardType.AQI,
        CardType.UV,
        CardType.HUMIDITY,
    ),

    UserPersonaType.PARENTS_FAMILIES: (
        CardType.FAMILY_SCHOOL,
        CardType.COMMUTE_CONDITIONS,
        CardType.WEATHER_CONDITION,
        CardType.RAINFALL,
        CardType.AQI,
        CardType.TEMPERATURE,
        CardType.WIND,
        CardType.UV,
        CardType.HUMIDITY,
    ),

    UserPersonaType.FARMER: (
        CardType.SOIL_MOISTURE,
        CardType.RAINFALL,
        CardType.HUMIDITY,
        CardType.WEATHER_CONDITION,
        CardType.WIND,
        CardType.TEMPERATURE,
        CardType.UV,
    ),

    UserPersonaType.COMMUTER: (
        CardType.COMMUTE_CONDITIONS,
        CardType.WEATHER_CONDITION,
        CardType.RAINFALL,
        CardType.AQI,
        CardType.WIND,
        CardType.TEMPERATURE,
        CardType.HUMIDITY,
    ),

    UserPersonaType.EVENT_PLANNER: (
        CardType.EVENT_CONDITIONS,
        CardType.COMMUTE_CONDITIONS,
        CardType.WEATHER_CONDITION,
        CardType.RAINFALL,
        CardType.WIND,
        CardType.TEMPERATURE,
        CardType.UV,
        CardType.HUMIDITY,
        CardType.AQI,
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