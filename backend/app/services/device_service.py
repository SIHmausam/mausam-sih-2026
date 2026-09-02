import uuid
from datetime import (
    UTC,
    datetime,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    DevicePlatform,
    PushRegistrationType,
)
from app.models.device_registration import (
    DeviceRegistration,
)
from app.repositories.device_repository import (
    DeviceRepository,
)


class DeviceNotFoundError(Exception):
    pass


class DeviceService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.repository = DeviceRepository(session)

    async def register_device(
        self,
        *,
        user_id: uuid.UUID,
        registration_id: str,
        registration_type: PushRegistrationType,
        platform: DevicePlatform,
        device_name: str | None = None,
    ) -> DeviceRegistration:
        now = datetime.now(UTC)

        existing = await self.repository.get_by_registration_id(
            registration_id=(registration_id)
        )

        if existing is not None:
            # Reassigning is intentional:
            #
            # User A logs out on the phone.
            # User B logs in on the same phone.
            # The installation should now belong
            # to User B.
            existing.user_id = user_id

            existing.registration_type = registration_type.value

            existing.platform = platform.value

            existing.device_name = device_name

            existing.is_active = True
            existing.last_seen_at = now

            await self.session.commit()

            await self.session.refresh(existing)

            return existing

        registration = DeviceRegistration(
            user_id=user_id,
            registration_id=(registration_id),
            registration_type=(registration_type.value),
            platform=platform.value,
            device_name=device_name,
            is_active=True,
            last_seen_at=now,
        )

        await self.repository.create(registration)

        await self.session.commit()

        await self.session.refresh(registration)

        return registration

    async def list_devices(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[DeviceRegistration]:
        return await self.repository.list_for_user(
            user_id=user_id,
            active_only=True,
        )

    async def unregister_device(
        self,
        *,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> None:
        registration = await self.repository.get_owned(
            device_id=device_id,
            user_id=user_id,
        )

        if registration is None:
            raise DeviceNotFoundError("Device registration not found")

        if not registration.is_active:
            return

        registration.is_active = False

        await self.session.commit()
