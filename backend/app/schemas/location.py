import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import LocationType


class LocationCreateRequest(BaseModel):
    label: str = Field(
        min_length=1,
        max_length=100,
    )

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    location_type: LocationType

    is_primary: bool = False


class LocationUpdateRequest(BaseModel):
    label: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    location_type: LocationType | None = None

    is_primary: bool | None = None


class LocationResponse(BaseModel):
    id: uuid.UUID
    label: str
    latitude: float
    longitude: float
    location_type: LocationType
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
