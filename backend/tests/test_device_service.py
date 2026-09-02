import uuid
from datetime import (
    UTC,
    datetime,
)
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    DevicePlatform,
    PushRegistrationType,
)
from app.models.device_registration import (
    DeviceRegistration,
)
from app.services.device_service import (
    DeviceNotFoundError,
    DeviceService,
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


class FakeDeviceRepository:
    def __init__(self):
        self.devices: list[DeviceRegistration] = []

    async def get_by_registration_id(
        self,
        *,
        registration_id: str,
    ) -> DeviceRegistration | None:
        for device in self.devices:
            if device.registration_id == registration_id:
                return device

        return None

    async def get_owned(
        self,
        *,
        device_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DeviceRegistration | None:
        for device in self.devices:
            if device.id == device_id and device.user_id == user_id:
                return device

        return None

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        active_only: bool = True,
    ) -> list[DeviceRegistration]:
        devices = [device for device in self.devices if device.user_id == user_id]

        if active_only:
            devices = [device for device in devices if device.is_active]

        return devices

    async def create(
        self,
        registration: DeviceRegistration,
    ) -> DeviceRegistration:
        if registration.id is None:
            registration.id = uuid.uuid4()

        if registration.created_at is None:
            registration.created_at = datetime.now(UTC)

        if registration.updated_at is None:
            registration.updated_at = datetime.now(UTC)

        self.devices.append(registration)

        return registration


def build_service() -> tuple[
    DeviceService,
    FakeSession,
    FakeDeviceRepository,
]:
    session = FakeSession()

    service = DeviceService(
        cast(
            AsyncSession,
            session,
        )
    )

    repository = FakeDeviceRepository()

    service.repository = repository

    return (
        service,
        session,
        repository,
    )


@pytest.mark.asyncio
async def test_register_new_device():
    (
        service,
        session,
        repository,
    ) = build_service()

    user_id = uuid.uuid4()

    device = await service.register_device(
        user_id=user_id,
        registration_id="firebase-fid-123",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
        device_name="Raman Phone",
    )

    assert device.id is not None
    assert device.user_id == user_id

    assert device.registration_id == "firebase-fid-123"

    assert device.registration_type == PushRegistrationType.FID.value

    assert device.platform == DevicePlatform.ANDROID.value

    assert device.is_active is True

    assert len(repository.devices) == 1

    assert session.commit_calls == 1
    assert session.refresh_calls == 1


@pytest.mark.asyncio
async def test_register_existing_device_is_idempotent():
    (
        service,
        _session,
        repository,
    ) = build_service()

    user_id = uuid.uuid4()

    first = await service.register_device(
        user_id=user_id,
        registration_id="same-device",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
    )

    second = await service.register_device(
        user_id=user_id,
        registration_id="same-device",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
    )

    assert first.id == second.id

    assert len(repository.devices) == 1


@pytest.mark.asyncio
async def test_device_can_be_reassigned_to_new_user():
    (
        service,
        _session,
        repository,
    ) = build_service()

    first_user = uuid.uuid4()
    second_user = uuid.uuid4()

    device = await service.register_device(
        user_id=first_user,
        registration_id="shared-phone",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
    )

    updated = await service.register_device(
        user_id=second_user,
        registration_id="shared-phone",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
    )

    assert updated.id == device.id

    assert updated.user_id == second_user

    assert len(repository.devices) == 1


@pytest.mark.asyncio
async def test_unregister_device():
    (
        service,
        _session,
        _repository,
    ) = build_service()

    user_id = uuid.uuid4()

    device = await service.register_device(
        user_id=user_id,
        registration_id="device-to-remove",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
    )

    await service.unregister_device(
        user_id=user_id,
        device_id=device.id,
    )

    assert device.is_active is False


@pytest.mark.asyncio
async def test_user_cannot_unregister_another_users_device():
    (
        service,
        _session,
        _repository,
    ) = build_service()

    owner_id = uuid.uuid4()

    device = await service.register_device(
        user_id=owner_id,
        registration_id="private-device",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
    )

    with pytest.raises(
        DeviceNotFoundError,
        match=("Device registration not found"),
    ):
        await service.unregister_device(
            user_id=uuid.uuid4(),
            device_id=device.id,
        )


@pytest.mark.asyncio
async def test_list_devices_only_returns_users_active_devices():
    (
        service,
        _session,
        _repository,
    ) = build_service()

    user_id = uuid.uuid4()

    active = await service.register_device(
        user_id=user_id,
        registration_id="active-device",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
    )

    inactive = await service.register_device(
        user_id=user_id,
        registration_id="inactive-device",
        registration_type=(PushRegistrationType.FID),
        platform=(DevicePlatform.ANDROID),
    )

    await service.unregister_device(
        user_id=user_id,
        device_id=inactive.id,
    )

    devices = await service.list_devices(user_id=user_id)

    assert len(devices) == 1

    assert devices[0].id == active.id
