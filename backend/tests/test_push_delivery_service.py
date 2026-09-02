import uuid
from datetime import (
    UTC,
    datetime,
)
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.enums import (
    PushRegistrationType,
)
from app.integrations.push.base import (
    InvalidPushRegistrationError,
    PushMessage,
    PushProvider,
    PushSendResult,
    TemporaryPushProviderError,
)
from app.models.device_registration import (
    DeviceRegistration,
)
from app.models.notification import (
    Notification,
)
from app.services.push_delivery_service import (
    PushDeliveryService,
)


class FakeSession:
    def __init__(self):
        self.commit_calls = 0

    async def commit(self):
        self.commit_calls += 1


class FakeDeviceRepository:
    def __init__(
        self,
        devices: list[DeviceRegistration],
    ):
        self.devices = devices

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        active_only: bool = True,
    ):
        devices = [device for device in self.devices if device.user_id == user_id]

        if active_only:
            devices = [device for device in devices if device.is_active]

        return devices


class FakePushProvider(PushProvider):
    def __init__(
        self,
        *,
        invalid_ids: set[str] | None = None,
        temporary_failures: (set[str] | None) = None,
    ):
        self.invalid_ids = invalid_ids or set()

        self.temporary_failures = temporary_failures or set()

        self.calls: list[
            tuple[
                str,
                PushRegistrationType,
                PushMessage,
            ]
        ] = []

    async def send(
        self,
        *,
        registration_id: str,
        registration_type: (PushRegistrationType),
        message: PushMessage,
    ) -> PushSendResult:
        self.calls.append(
            (
                registration_id,
                registration_type,
                message,
            )
        )

        if registration_id in self.invalid_ids:
            raise (InvalidPushRegistrationError())

        if registration_id in self.temporary_failures:
            raise (TemporaryPushProviderError())

        return PushSendResult(message_id="firebase-message")


def build_device(
    *,
    user_id: uuid.UUID,
    registration_id: str,
) -> DeviceRegistration:
    return DeviceRegistration(
        id=uuid.uuid4(),
        user_id=user_id,
        registration_id=(registration_id),
        registration_type=(PushRegistrationType.FID.value),
        platform="android",
        is_active=True,
        last_seen_at=datetime.now(UTC),
    )


def build_notification(
    *,
    user_id: uuid.UUID,
) -> Notification:
    return Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        notification_type="aqi_alert",
        title="Unhealthy air quality",
        message="Current AQI is 163.",
        severity="warning",
        source="open_meteo",
        source_reference="aqi:test",
        is_read=False,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_push_sent_to_all_active_devices():
    user_id = uuid.uuid4()

    devices = [
        build_device(
            user_id=user_id,
            registration_id="fid-1",
        ),
        build_device(
            user_id=user_id,
            registration_id="fid-2",
        ),
    ]

    session = FakeSession()
    provider = FakePushProvider()

    service = PushDeliveryService(
        session=cast(
            AsyncSession,
            session,
        ),
        provider=provider,
    )

    service.device_repository = FakeDeviceRepository(devices)

    result = await service.deliver_notification(
        user_id=user_id,
        notification=(build_notification(user_id=user_id)),
    )

    assert result.attempted == 2
    assert result.sent == 2
    assert result.failed == 0

    assert len(provider.calls) == 2


@pytest.mark.asyncio
async def test_invalid_registration_is_deactivated():
    user_id = uuid.uuid4()

    device = build_device(
        user_id=user_id,
        registration_id="dead-fid",
    )

    session = FakeSession()

    provider = FakePushProvider(invalid_ids={"dead-fid"})

    service = PushDeliveryService(
        session=cast(
            AsyncSession,
            session,
        ),
        provider=provider,
    )

    service.device_repository = FakeDeviceRepository([device])

    result = await service.deliver_notification(
        user_id=user_id,
        notification=(build_notification(user_id=user_id)),
    )

    assert result.sent == 0
    assert result.failed == 1
    assert result.deactivated == 1

    assert device.is_active is False

    assert session.commit_calls == 1


@pytest.mark.asyncio
async def test_temporary_failure_keeps_device_active():
    user_id = uuid.uuid4()

    device = build_device(
        user_id=user_id,
        registration_id="temporary-fid",
    )

    session = FakeSession()

    provider = FakePushProvider(temporary_failures={"temporary-fid"})

    service = PushDeliveryService(
        session=cast(
            AsyncSession,
            session,
        ),
        provider=provider,
    )

    service.device_repository = FakeDeviceRepository([device])

    result = await service.deliver_notification(
        user_id=user_id,
        notification=(build_notification(user_id=user_id)),
    )

    assert result.failed == 1

    assert device.is_active is True

    assert session.commit_calls == 0
