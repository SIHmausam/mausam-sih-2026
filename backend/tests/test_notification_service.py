import uuid
from datetime import UTC, datetime
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    NotificationSeverity,
    NotificationType,
)
from app.models.notification import Notification
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationService,
)


class FakeSession:
    def __init__(self):
        self.commit_calls = 0
        self.refresh_calls = 0

    async def commit(self):
        self.commit_calls += 1

    async def refresh(
        self,
        _instance,
    ):
        self.refresh_calls += 1


class FakeNotificationRepository:
    def __init__(self):
        self.notifications: list[Notification] = []

    async def create(
        self,
        notification: Notification,
    ) -> Notification:
        if notification.id is None:
            notification.id = uuid.uuid4()

        if notification.created_at is None:
            notification.created_at = datetime.now(UTC)

        self.notifications.append(notification)

        return notification

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        notifications = [
            notification
            for notification in self.notifications
            if notification.user_id == user_id
        ]

        if unread_only:
            notifications = [
                notification
                for notification in notifications
                if not notification.is_read
            ]

        notifications.sort(
            key=lambda notification: notification.created_at,
            reverse=True,
        )

        return notifications[offset : offset + limit]

    async def get_owned(
        self,
        *,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Notification | None:
        for notification in self.notifications:
            if notification.id == notification_id and notification.user_id == user_id:
                return notification

        return None

    async def unread_count(
        self,
        *,
        user_id: uuid.UUID,
    ) -> int:
        return sum(
            1
            for notification in self.notifications
            if (notification.user_id == user_id and not notification.is_read)
        )

    async def mark_all_read(
        self,
        *,
        user_id: uuid.UUID,
        read_at: datetime,
    ) -> int:
        updated_count = 0

        for notification in self.notifications:
            if notification.user_id != user_id or notification.is_read:
                continue

            notification.is_read = True
            notification.read_at = read_at

            updated_count += 1

        return updated_count


def build_service() -> tuple[
    NotificationService,
    FakeSession,
    FakeNotificationRepository,
]:
    session = FakeSession()

    service = NotificationService(
        cast(
            AsyncSession,
            session,
        )
    )

    repository = FakeNotificationRepository()

    service.repository = repository

    return (
        service,
        session,
        repository,
    )


@pytest.mark.asyncio
async def test_create_notification():
    (
        service,
        session,
        repository,
    ) = build_service()

    user_id = uuid.uuid4()
    location_id = uuid.uuid4()

    notification = await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.OFFICIAL_ALERT),
        title=("Severe weather warning"),
        message=("A severe weather alert is active for your area."),
        severity=(NotificationSeverity.CRITICAL),
        source="sachet",
        related_location_id=(location_id),
        source_reference=("ALERT-001"),
    )

    assert notification.id is not None

    assert notification.user_id == user_id

    assert notification.notification_type == NotificationType.OFFICIAL_ALERT.value

    assert notification.severity == NotificationSeverity.CRITICAL.value

    assert notification.source == "sachet"

    assert notification.related_location_id == location_id

    assert notification.source_reference == "ALERT-001"

    assert notification.is_read is False

    assert notification.read_at is None

    assert len(repository.notifications) == 1

    assert session.commit_calls == 1
    assert session.refresh_calls == 1


@pytest.mark.asyncio
async def test_list_notifications_only_for_user():
    (
        service,
        _session,
        _repository,
    ) = build_service()

    first_user = uuid.uuid4()
    second_user = uuid.uuid4()

    await service.create_notification(
        user_id=first_user,
        notification_type=(NotificationType.AQI_ALERT),
        title="AQI warning",
        message="AQI is unhealthy.",
        severity=(NotificationSeverity.WARNING),
    )

    await service.create_notification(
        user_id=first_user,
        notification_type=(NotificationType.RAIN_ALERT),
        title="Rain expected",
        message="Rain is expected today.",
        severity=(NotificationSeverity.CAUTION),
    )

    await service.create_notification(
        user_id=second_user,
        notification_type=(NotificationType.DAILY_SUMMARY),
        title="Daily summary",
        message="Your daily weather summary.",
    )

    notifications = await service.list_notifications(user_id=first_user)

    assert len(notifications) == 2

    assert all(notification.user_id == first_user for notification in notifications)


@pytest.mark.asyncio
async def test_list_only_unread_notifications():
    (
        service,
        _session,
        repository,
    ) = build_service()

    user_id = uuid.uuid4()

    first = await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.AQI_ALERT),
        title="AQI warning",
        message="AQI is unhealthy.",
    )

    await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.RAIN_ALERT),
        title="Rain alert",
        message="Rain is expected.",
    )

    first.is_read = True
    first.read_at = datetime.now(UTC)

    assert len(repository.notifications) == 2

    notifications = await service.list_notifications(
        user_id=user_id,
        unread_only=True,
    )

    assert len(notifications) == 1

    assert notifications[0].notification_type == NotificationType.RAIN_ALERT.value


@pytest.mark.asyncio
async def test_unread_count():
    (
        service,
        _session,
        _repository,
    ) = build_service()

    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    first = await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.ROUTINE_WARNING),
        title="Routine warning",
        message=("Your morning run may be affected."),
    )

    await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.AQI_ALERT),
        title="AQI alert",
        message="AQI is unhealthy.",
    )

    await service.create_notification(
        user_id=other_user_id,
        notification_type=(NotificationType.RAIN_ALERT),
        title="Rain alert",
        message="Rain is expected.",
    )

    first.is_read = True
    first.read_at = datetime.now(UTC)

    count = await service.get_unread_count(user_id=user_id)

    assert count == 1


@pytest.mark.asyncio
async def test_mark_notification_read():
    (
        service,
        session,
        _repository,
    ) = build_service()

    user_id = uuid.uuid4()

    notification = await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.AQI_ALERT),
        title="AQI warning",
        message="AQI is unhealthy.",
    )

    commit_count_before = session.commit_calls

    result = await service.mark_read(
        user_id=user_id,
        notification_id=(notification.id),
    )

    assert result.is_read is True

    assert result.read_at is not None

    assert session.commit_calls == commit_count_before + 1


@pytest.mark.asyncio
async def test_mark_already_read_notification_is_idempotent():
    (
        service,
        session,
        _repository,
    ) = build_service()

    user_id = uuid.uuid4()

    notification = await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.DAILY_SUMMARY),
        title="Daily summary",
        message="Weather summary.",
    )

    await service.mark_read(
        user_id=user_id,
        notification_id=(notification.id),
    )

    commit_count = session.commit_calls

    read_at = notification.read_at

    result = await service.mark_read(
        user_id=user_id,
        notification_id=(notification.id),
    )

    assert result.is_read is True

    assert result.read_at == read_at

    # No additional database write.
    assert session.commit_calls == commit_count


@pytest.mark.asyncio
async def test_user_cannot_mark_another_users_notification_read():
    (
        service,
        _session,
        _repository,
    ) = build_service()

    owner_id = uuid.uuid4()
    another_user_id = uuid.uuid4()

    notification = await service.create_notification(
        user_id=owner_id,
        notification_type=(NotificationType.OFFICIAL_ALERT),
        title="Official warning",
        message=("A warning is active."),
    )

    with pytest.raises(
        NotificationNotFoundError,
        match="Notification not found",
    ):
        await service.mark_read(
            user_id=another_user_id,
            notification_id=(notification.id),
        )


@pytest.mark.asyncio
async def test_mark_all_notifications_read():
    (
        service,
        _session,
        _repository,
    ) = build_service()

    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    first = await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.RAIN_ALERT),
        title="Rain alert",
        message="Rain expected.",
    )

    second = await service.create_notification(
        user_id=user_id,
        notification_type=(NotificationType.AQI_ALERT),
        title="AQI warning",
        message="AQI unhealthy.",
    )

    other = await service.create_notification(
        user_id=other_user_id,
        notification_type=(NotificationType.AQI_ALERT),
        title="AQI warning",
        message="AQI unhealthy.",
    )

    updated_count = await service.mark_all_read(user_id=user_id)

    assert updated_count == 2

    assert first.is_read is True
    assert second.is_read is True

    assert first.read_at is not None
    assert second.read_at is not None

    # Another user's notification
    # must remain untouched.
    assert other.is_read is False
    assert other.read_at is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "notification_type",
    list(NotificationType),
)
async def test_all_notification_types_are_supported(
    notification_type: NotificationType,
):
    (
        service,
        _session,
        _repository,
    ) = build_service()

    notification = await service.create_notification(
        user_id=uuid.uuid4(),
        notification_type=(notification_type),
        title="Test notification",
        message="Test message",
    )

    assert notification.notification_type == notification_type.value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "severity",
    list(NotificationSeverity),
)
async def test_all_notification_severities_are_supported(
    severity: NotificationSeverity,
):
    (
        service,
        _session,
        _repository,
    ) = build_service()

    notification = await service.create_notification(
        user_id=uuid.uuid4(),
        notification_type=(NotificationType.OFFICIAL_ALERT),
        title="Test notification",
        message="Test message",
        severity=severity,
    )

    assert notification.severity == severity.value
