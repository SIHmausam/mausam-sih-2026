import uuid
from dataclasses import dataclass

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
    PushProviderError,
    TemporaryPushProviderError,
)
from app.models.notification import (
    Notification,
)
from app.repositories.device_repository import (
    DeviceRepository,
)


@dataclass(frozen=True)
class PushDeliverySummary:
    attempted: int
    sent: int
    failed: int
    deactivated: int


class PushDeliveryService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        provider: PushProvider,
    ):
        self.session = session
        self.provider = provider

        self.device_repository = DeviceRepository(session)

    @staticmethod
    def _message(
        notification: Notification,
    ) -> PushMessage:
        data = {
            "notification_id": str(notification.id),
            "notification_type": (notification.notification_type),
        }

        if notification.source:
            data["source"] = notification.source

        if notification.source_reference:
            data["source_reference"] = notification.source_reference

        if notification.related_location_id is not None:
            data["location_id"] = str(notification.related_location_id)

        return PushMessage(
            title=notification.title,
            body=notification.message,
            data=data,
        )

    async def deliver_notification(
        self,
        *,
        user_id: uuid.UUID,
        notification: Notification,
    ) -> PushDeliverySummary:
        devices = await self.device_repository.list_for_user(
            user_id=user_id,
            active_only=True,
        )

        message = self._message(notification)

        attempted = 0
        sent = 0
        failed = 0
        deactivated = 0

        for device in devices:
            attempted += 1

            try:
                registration_type = PushRegistrationType(device.registration_type)

                await self.provider.send(
                    registration_id=(device.registration_id),
                    registration_type=(registration_type),
                    message=message,
                )

                sent += 1

            except InvalidPushRegistrationError:
                # FCM says this app installation
                # is no longer registered.
                device.is_active = False

                deactivated += 1
                failed += 1

            except (
                TemporaryPushProviderError,
                PushProviderError,
            ):
                # Notification remains available
                # in the in-app inbox even when
                # push delivery fails.
                failed += 1

        if deactivated > 0:
            await self.session.commit()

        return PushDeliverySummary(
            attempted=attempted,
            sent=sent,
            failed=failed,
            deactivated=deactivated,
        )
