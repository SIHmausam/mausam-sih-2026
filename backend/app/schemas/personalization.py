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
    "health_conscious",
    "fitness",
    "surfer",
    "traveler",
    "parents_families",
    "farmer",
    "commuter",
    "event_planner",
]


MLCardType = Literal[
    "temperature",
    "weather_conditions",
    "humidity",
    "rain_forecast",
    "wind",
    "air_quality",
    "uv_allergy",
    "running_conditions",
    "surf_conditions",
    "tide_water",
    "farm_garden",
    "commute_conditions",
    "travel_conditions",
    "family_school",
    "event_conditions",
]


MLInteractionAction = Literal[
    "view",
    "click",
    "expand",
    "dismiss",
]


class MLInteractionRequest(BaseModel):
    user_id: str

    card_id: MLCardType

    action: MLInteractionAction

    timestamp: datetime

    position: int = Field(
        ge=1,
        le=15,
    )

    session_id: str = Field(
        min_length=1,
        max_length=100,
    )


class MLWeatherFeatures(BaseModel):

    city: str
    timestamp: datetime

    temperature_2m: float
    relative_humidity_2m: float
    dew_point_2m: float
    apparent_temperature: float

    precipitation: float
    rain: float

    weather_code: int
    cloud_cover: float

    wind_speed_10m: float
    wind_direction_10m: float
    wind_gusts_10m: float

    soil_moisture_0_to_7cm: float
    soil_moisture_7_to_28cm: float
    soil_moisture_28_to_100cm: float
    soil_moisture_100_to_255cm: float

    soil_temperature_0_to_7cm: float
    soil_temperature_7_to_28cm: float
    soil_temperature_28_to_100cm: float
    soil_temperature_100_to_255cm: float

    et0_fao_evapotranspiration: float

    precipitation_hours: float
    precipitation_probability: float

    showers: float
    visibility: float

    european_aqi: float
    us_aqi: float

    uv_index: float
    uv_index_clear_sky: float

    pm2_5: float
    pm10: float

    nitrogen_dioxide: float
    sulphur_dioxide: float
    carbon_monoxide: float
    ozone: float

    wave_height: float | None = None
    wave_direction: float | None = None
    wave_period: float | None = None

    swell_wave_height: float | None = None
    swell_wave_direction: float | None = None
    swell_wave_period: float | None = None

    sea_level_height_msl: float | None = None
    sea_surface_temperature: float | None = None

    marine_data_available: bool

    sunrise: datetime
    sunset: datetime

    is_daylight: bool


class MLPersonalizationRequest(BaseModel):
    user_id: str

    personas: list[MLPersona] = Field(
        min_length=1,
        max_length=3,
    )

    weather: MLWeatherFeatures


class MLRankedCard(BaseModel):
    rank: int = Field(
        ge=1,
        le=15,
    )

    card: MLCardType

    score: float = Field(
        ge=0,
        le=1,
    )

    insight: str


class MLPersonalizationResponse(BaseModel):
    city: str

    personas: list[MLPersona] = Field(
        min_length=1,
        max_length=3,
    )

    cards: list[MLRankedCard]

    @model_validator(mode="after")
    def validate_card_ranking(
        self,
    ):
        if not self.cards:
            raise ValueError(
                "ML personalization response "
                "must contain at least one card"
            )

        if len(self.cards) > 15:
            raise ValueError(
                "ML personalization response "
                "cannot contain more than 15 cards"
            )

        card_names = [
            item.card
            for item in self.cards
        ]

        if len(set(card_names)) != len(card_names):
            raise ValueError(
                "ML personalization response "
                "contains duplicate cards"
            )

        ranks = sorted(
            item.rank
            for item in self.cards
        )

        expected_ranks = list(
            range(
                1,
                len(self.cards) + 1,
            )
        )

        if ranks != expected_ranks:
            raise ValueError(
                "ML personalization response "
                "contains invalid ranks"
            )

        return self


class PersonalizedCard(BaseModel):
    rank: int = Field(
        ge=1,
        le=15,
    )

    card: CardType

    score: float | None = None

    insight: str | None = None


class PersonalizationResult(BaseModel):
    location_id: str

    city: str

    # Keep the current public API backward-compatible.
    persona: UserPersonaType

    source: Literal[
        "ml",
        "fallback",
    ]

    cards: list[PersonalizedCard]