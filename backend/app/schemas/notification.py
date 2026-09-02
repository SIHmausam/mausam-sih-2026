import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    NotificationSeverity,
    NotificationType,
)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    notification_type: NotificationType
    title: str
    message: str
    severity: NotificationSeverity
    source: str | None
    related_location_id: uuid.UUID | None
    source_reference: str | None

    is_read: bool
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationReadResponse(BaseModel):
    id: uuid.UUID
    is_read: bool
    read_at: datetime | None


class NotificationReadAllResponse(BaseModel):
    updated_count: int
