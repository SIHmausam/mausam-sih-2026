import uuid
from datetime import date, datetime, time

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.core.enums import (
    ActivityContext,
    RoutineImpactLevel,
    Weekday,
)


class RoutineCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    activity_context: ActivityContext

    saved_location_id: uuid.UUID | None = None

    days_of_week: list[Weekday] = Field(
        min_length=1,
    )

    start_time: time

    duration_minutes: int = Field(
        ge=5,
        le=720,
    )

    is_enabled: bool = True

    @field_validator("days_of_week")
    @classmethod
    def validate_unique_days(
        cls,
        value: list[Weekday],
    ) -> list[Weekday]:
        if len(value) != len(set(value)):
            raise ValueError("days_of_week must not contain duplicates")

        return value


class RoutineUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    activity_context: ActivityContext | None = None

    saved_location_id: uuid.UUID | None = None

    days_of_week: list[Weekday] | None = Field(
        default=None,
        min_length=1,
    )

    start_time: time | None = None

    duration_minutes: int | None = Field(
        default=None,
        ge=5,
        le=720,
    )

    is_enabled: bool | None = None

    @field_validator("days_of_week")
    @classmethod
    def validate_unique_days(
        cls,
        value: list[Weekday] | None,
    ) -> list[Weekday] | None:
        if value is None:
            return None

        if len(value) != len(set(value)):
            raise ValueError("days_of_week must not contain duplicates")

        return value


class RoutineResponse(BaseModel):
    id: uuid.UUID

    name: str
    activity_context: ActivityContext

    saved_location_id: uuid.UUID | None

    days_of_week: list[Weekday]

    start_time: time
    duration_minutes: int

    is_enabled: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoutineLocationSummary(BaseModel):
    id: uuid.UUID
    label: str
    city: str

    latitude: float
    longitude: float


class RoutineWeatherSnapshot(BaseModel):
    temperature: float | None = None
    apparent_temperature: float | None = None

    humidity: float | None = None

    rain: float | None = None
    rain_probability: float | None = None

    wind_speed: float | None = None
    visibility: float | None = None

    aqi: float | None = None
    uv_index: float | None = None

    surface_soil_moisture: float | None = None


class MyDayRoutineItem(BaseModel):
    routine_id: uuid.UUID

    name: str
    activity_context: ActivityContext

    start_time: time
    duration_minutes: int

    location: RoutineLocationSummary | None = None

    impact: RoutineImpactLevel

    reasons: list[str] = Field(default_factory=list)

    recommendation: str

    weather: RoutineWeatherSnapshot | None = None


class MyDayResponse(BaseModel):
    date: date

    routines: list[MyDayRoutineItem]
