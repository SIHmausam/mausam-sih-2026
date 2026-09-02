import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.enums import LocationType
from app.schemas.air_quality import (
    CurrentAirQualityResponse,
)
from app.schemas.alert import OfficialAlert
from app.schemas.personalization import (
    PersonalizationResult,
)
from app.schemas.routine import MyDayResponse
from app.schemas.weather import (
    AgricultureContextResponse,
    CurrentWeatherResponse,
    DailyWeatherItem,
)


class HomepageLocation(BaseModel):
    id: uuid.UUID

    label: str
    city: str

    latitude: float
    longitude: float

    location_type: LocationType


class HomepageWeatherSummary(BaseModel):
    current: CurrentWeatherResponse

    air_quality: CurrentAirQualityResponse | None = None

    agriculture: AgricultureContextResponse | None = None

    today: DailyWeatherItem | None = None


class HomepageResponse(BaseModel):
    # Use this same ID for all card interaction
    # events generated from this homepage load.
    session_id: str

    generated_at: datetime

    location: HomepageLocation

    # True only for severe/extreme official
    # alerts. ML never controls this.
    has_safety_override: bool

    alerts: list[OfficialAlert]

    weather: HomepageWeatherSummary

    my_day: MyDayResponse

    personalization: PersonalizationResult
