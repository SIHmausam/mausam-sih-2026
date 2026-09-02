import uuid
from datetime import datetime

from sqlalchemy import (
    Select,
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        notification: Notification,
    ) -> Notification:
        self.session.add(notification)

        await self.session.flush()

        return notification

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        statement: Select[tuple[Notification]] = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if unread_only:
            statement = statement.where(Notification.is_read.is_(False))

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_owned(
        self,
        *,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def unread_count(
        self,
        *,
        user_id: uuid.UUID,
    ) -> int:
        result = await self.session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )

        return int(result.scalar_one())

    async def mark_all_read(
        self,
        *,
        user_id: uuid.UUID,
        read_at: datetime,
    ) -> int:
        result = await self.session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(
                is_read=True,
                read_at=read_at,
            )
        )

        return result.rowcount or 0

    async def get_by_source_reference(
        self,
        *,
        user_id: uuid.UUID,
        notification_type: str,
        source_reference: str,
    ) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.notification_type == notification_type,
                Notification.source_reference == source_reference,
            )
        )

        return result.scalar_one_or_none()
