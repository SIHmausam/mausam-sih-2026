from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from app.core.enums import (
    CardType,
    UserPersonaType,
)

MLPersona = Literal[
    "fitness",
    "farmer",
    "traveler",
]

MLCardType = Literal[
    "aqi",
    "uv",
    "temperature",
    "humidity",
    "rain",
    "wind",
    "soil_moisture",
    "weather_condition",
]


class MLWeatherFeatures(BaseModel):
    city: str

    timestamp: datetime

    temperature_2m: float
    relative_humidity_2m: float
    apparent_temperature: float

    precipitation: float
    rain: float

    weather_code: int

    wind_speed_10m: float

    soil_moisture_0_to_7cm: float

    us_aqi: float
    european_aqi: float

    uv_index: float

    pm2_5: float
    pm10: float

    nitrogen_dioxide: float
    sulphur_dioxide: float
    carbon_monoxide: float
    ozone: float

    # Currently required by the ML HTTP API,
    # although they are not all model features.
    sunrise: datetime | None = None
    sunset: datetime | None = None
    is_daylight: bool | None = None


class MLPersonalizationRequest(BaseModel):
    user_id: str

    persona: MLPersona

    weather: MLWeatherFeatures


class MLRankedCard(BaseModel):
    rank: int = Field(
        ge=1,
        le=8,
    )

    card: MLCardType

    score: float = Field(
        ge=0,
        le=1,
    )

    insight: str


class MLPersonalizationResponse(BaseModel):
    city: str

    persona: MLPersona

    cards: list[MLRankedCard]

    @model_validator(mode="after")
    def validate_card_ranking(
        self,
    ):
        if len(self.cards) != 8:
            raise ValueError("ML personalization response must contain exactly 8 cards")

        card_names = [item.card for item in self.cards]

        if len(set(card_names)) != 8:
            raise ValueError("ML personalization response contains duplicate cards")

        ranks = sorted(item.rank for item in self.cards)

        if ranks != list(range(1, 9)):
            raise ValueError(
                "ML personalization response must contain ranks 1 through 8"
            )

        return self


class PersonalizedCard(BaseModel):
    rank: int = Field(
        ge=1,
        le=8,
    )

    card: CardType

    # ML provides a score.
    # Deterministic fallback intentionally does not.
    score: float | None = None

    insight: str | None = None


class PersonalizationResult(BaseModel):
    location_id: str

    city: str

    persona: UserPersonaType

    source: Literal[
        "ml",
        "fallback",
    ]

    cards: list[PersonalizedCard]
