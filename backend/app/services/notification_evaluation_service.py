import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    NotificationSeverity,
    NotificationType,
)
from app.repositories.preference_repository import (
    PreferenceRepository,
)
from app.schemas.alert import OfficialAlert
from app.services.notification_service import (
    NotificationService,
)


class NotificationEvaluationService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.preference_repository = PreferenceRepository(session)

        self.notification_service = NotificationService(session)

    @staticmethod
    def _is_severe_official_alert(
        alert: OfficialAlert,
    ) -> bool:
        severity = (alert.severity or "").casefold()

        return severity in {
            "severe",
            "extreme",
        }

    @staticmethod
    def _notification_severity(
        alert: OfficialAlert,
    ) -> NotificationSeverity:
        severity = (alert.severity or "").casefold()

        if severity == "extreme":
            return NotificationSeverity.CRITICAL

        return NotificationSeverity.WARNING

    @staticmethod
    def _title(
        alert: OfficialAlert,
    ) -> str:
        if alert.headline:
            return alert.headline

        if alert.event:
            return f"Official {alert.event} alert"

        return "Official weather alert"

    @staticmethod
    def _message(
        alert: OfficialAlert,
    ) -> str:
        if alert.instruction:
            return alert.instruction

        if alert.description:
            return alert.description

        if alert.event:
            return f"An official {alert.event} warning is active for your area."

        return "An official weather warning is active for your area."

    async def evaluate_official_alerts(
        self,
        *,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
        alerts: list[OfficialAlert],
    ) -> int:
        """
        Create notifications for active Severe/Extreme
        SACHET alerts.

        Returns the number of newly created notifications.
        """

        preference = await self.preference_repository.get_preference(user_id)

        if preference is None:
            return 0

        if not (preference.official_alerts_enabled):
            return 0

        created_count = 0

        for alert in alerts:
            if not (self._is_severe_official_alert(alert)):
                continue

            _, created = await self.notification_service.create_notification_once(
                user_id=user_id,
                notification_type=(NotificationType.OFFICIAL_ALERT),
                title=self._title(alert),
                message=self._message(alert),
                severity=(self._notification_severity(alert)),
                source="sachet",
                related_location_id=(location_id),
                source_reference=(alert.identifier),
            )

            if created:
                created_count += 1

        return created_count
