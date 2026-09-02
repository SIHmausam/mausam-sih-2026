import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.core.enums import (
    DevicePlatform,
    PushRegistrationType,
)


class DeviceRegistrationRequest(BaseModel):
    registration_id: str = Field(
        min_length=1,
        max_length=512,
    )

    registration_type: PushRegistrationType

    platform: DevicePlatform

    device_name: str | None = Field(
        default=None,
        max_length=120,
    )


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    registration_type: PushRegistrationType
    platform: DevicePlatform
    device_name: str | None

    is_active: bool

    last_seen_at: datetime
    created_at: datetime


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]
