import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    NotificationSeverity,
    NotificationType,
    RoutineImpactLevel,
)
from app.repositories.preference_repository import (
    PreferenceRepository,
)
from app.schemas.alert import OfficialAlert
from app.schemas.routine import MyDayResponse
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

    @staticmethod
    def _routine_notification_severity(
        impact: RoutineImpactLevel,
    ) -> NotificationSeverity:
        if impact == RoutineImpactLevel.AVOID:
            return NotificationSeverity.WARNING

        return NotificationSeverity.CAUTION

    @staticmethod
    def _routine_title(
        *,
        routine_name: str,
        impact: RoutineImpactLevel,
    ) -> str:
        if impact == RoutineImpactLevel.AVOID:
            return f"Avoid {routine_name}"

        return f"Caution for {routine_name}"

    @staticmethod
    def _routine_message(
        *,
        reasons: list[str],
        recommendation: str,
    ) -> str:
        parts: list[str] = []

        if reasons:
            parts.append(reasons[0])

        if recommendation:
            parts.append(recommendation)

        if not parts:
            return "Weather conditions may affect your planned routine."

        return " ".join(parts)

    async def evaluate_routine_impacts(
        self,
        *,
        user_id: uuid.UUID,
        my_day: MyDayResponse,
    ) -> int:
        """
        Create notifications for CAUTION and AVOID
        routine impacts.

        SAFE and UNAVAILABLE routines are not weather
        warning notifications.
        """

        preference = await self.preference_repository.get_preference(user_id)

        if preference is None:
            return 0

        if not preference.routine_alerts_enabled:
            return 0

        created_count = 0

        for routine in my_day.routines:
            if routine.impact not in {
                RoutineImpactLevel.CAUTION,
                RoutineImpactLevel.AVOID,
            }:
                continue

            source_reference = f"routine:{routine.routine_id}:{my_day.date.isoformat()}"

            location_id = routine.location.id if routine.location is not None else None

            _, created = await self.notification_service.create_notification_once(
                user_id=user_id,
                notification_type=(NotificationType.ROUTINE_WARNING),
                title=self._routine_title(
                    routine_name=routine.name,
                    impact=routine.impact,
                ),
                message=self._routine_message(
                    reasons=routine.reasons,
                    recommendation=(routine.recommendation),
                ),
                severity=(self._routine_notification_severity(routine.impact)),
                source="my_day",
                related_location_id=(location_id),
                source_reference=(source_reference),
            )

            if created:
                created_count += 1

        return created_count
