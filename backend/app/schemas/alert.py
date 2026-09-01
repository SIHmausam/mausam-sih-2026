import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AlertCoordinate(BaseModel):
    latitude: float
    longitude: float


class AlertPolygon(BaseModel):
    points: list[AlertCoordinate]


class AlertCircle(BaseModel):
    center: AlertCoordinate
    radius_km: float


class AlertGeocode(BaseModel):
    value_name: str
    value: str


class AlertArea(BaseModel):
    description: str | None = None

    polygons: list[AlertPolygon] = Field(default_factory=list)

    circles: list[AlertCircle] = Field(default_factory=list)

    geocodes: list[AlertGeocode] = Field(default_factory=list)


class AlertFeedItem(BaseModel):
    identifier: str | None = None

    title: str
    description: str | None = None
    link: str | None = None

    published_at: datetime | None = None


class AlertFeedResponse(BaseModel):
    alerts: list[AlertFeedItem]


class OfficialAlert(BaseModel):
    identifier: str

    event: str | None = None
    headline: str | None = None
    description: str | None = None
    instruction: str | None = None

    severity: str | None = None
    urgency: str | None = None
    certainty: str | None = None

    effective_at: datetime | None = None
    onset_at: datetime | None = None
    expires_at: datetime | None = None

    area_description: str | None = None

    areas: list[AlertArea] = Field(default_factory=list)

    sender_name: str | None = None


class RelevantAlertResponse(BaseModel):
    latitude: float
    longitude: float

    alerts: list[OfficialAlert]


class SavedLocationAlertResponse(BaseModel):
    location_id: uuid.UUID

    label: str
    city: str

    latitude: float
    longitude: float

    alerts: list[OfficialAlert]
