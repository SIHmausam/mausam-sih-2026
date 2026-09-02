import uuid
from datetime import (
    UTC,
    datetime,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    NotificationSeverity,
    NotificationType,
)
from app.models.notification import Notification
from app.repositories.notification_repository import (
    NotificationRepository,
)


class NotificationNotFoundError(Exception):
    pass


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.repository = NotificationRepository(session)

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        severity: NotificationSeverity = (NotificationSeverity.INFO),
        source: str | None = None,
        related_location_id: (uuid.UUID | None) = None,
        source_reference: (str | None) = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=(notification_type.value),
            title=title,
            message=message,
            severity=severity.value,
            source=source,
            related_location_id=(related_location_id),
            source_reference=(source_reference),
            is_read=False,
            read_at=None,
        )

        await self.repository.create(notification)

        await self.session.commit()

        await self.session.refresh(notification)

        return notification

    async def list_notifications(
        self,
        *,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        return await self.repository.list_for_user(
            user_id=user_id,
            unread_only=(unread_only),
            limit=limit,
            offset=offset,
        )

    async def get_unread_count(
        self,
        *,
        user_id: uuid.UUID,
    ) -> int:
        return await self.repository.unread_count(user_id=user_id)

    async def mark_read(
        self,
        *,
        user_id: uuid.UUID,
        notification_id: uuid.UUID,
    ) -> Notification:
        notification = await self.repository.get_owned(
            notification_id=(notification_id),
            user_id=user_id,
        )

        if notification is None:
            raise (NotificationNotFoundError("Notification not found"))

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)

            await self.session.commit()

            await self.session.refresh(notification)

        return notification

    async def mark_all_read(
        self,
        *,
        user_id: uuid.UUID,
    ) -> int:
        updated_count = await self.repository.mark_all_read(
            user_id=user_id,
            read_at=datetime.now(UTC),
        )

        await self.session.commit()

        return updated_count

    async def create_notification_once(
        self,
        *,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        severity: NotificationSeverity = (NotificationSeverity.INFO),
        source: str | None = None,
        related_location_id: uuid.UUID | None = None,
        source_reference: str | None = None,
    ) -> tuple[Notification, bool]:
        """
        Create an idempotent notification.

        Returns:
            (notification, created)

        created=False means this notification already existed.
        """

        if source_reference is not None:
            existing = await self.repository.get_by_source_reference(
                user_id=user_id,
                notification_type=(notification_type.value),
                source_reference=(source_reference),
            )

            if existing is not None:
                return existing, False

        notification = await self.create_notification(
            user_id=user_id,
            notification_type=(notification_type),
            title=title,
            message=message,
            severity=severity,
            source=source,
            related_location_id=(related_location_id),
            source_reference=(source_reference),
        )

        return notification, True
