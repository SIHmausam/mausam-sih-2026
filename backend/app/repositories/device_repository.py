import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_registration import (
    DeviceRegistration,
)


class DeviceRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_registration_id(
        self,
        *,
        registration_id: str,
    ) -> DeviceRegistration | None:
        result = await self.session.execute(
            select(DeviceRegistration).where(
                DeviceRegistration.registration_id == registration_id
            )
        )

        return result.scalar_one_or_none()

    async def get_owned(
        self,
        *,
        device_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DeviceRegistration | None:
        result = await self.session.execute(
            select(DeviceRegistration).where(
                DeviceRegistration.id == device_id,
                DeviceRegistration.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        active_only: bool = True,
    ) -> list[DeviceRegistration]:
        statement = (
            select(DeviceRegistration)
            .where(DeviceRegistration.user_id == user_id)
            .order_by(DeviceRegistration.last_seen_at.desc())
        )

        if active_only:
            statement = statement.where(DeviceRegistration.is_active.is_(True))

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def create(
        self,
        registration: DeviceRegistration,
    ) -> DeviceRegistration:
        self.session.add(registration)

        await self.session.flush()

        return registration
