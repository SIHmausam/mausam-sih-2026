import uuid
from datetime import date

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
from app.schemas.weather import WeatherContextResponse
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

    @staticmethod
    def _aqi_band(
        aqi: float,
    ) -> (
        tuple[
            str,
            NotificationSeverity,
        ]
        | None
    ):
        """
        Return an alert-worthy AQI band.

        AQI below 101 does not generate a
        standalone notification.
        """

        if aqi >= 301:
            return (
                "hazardous",
                NotificationSeverity.CRITICAL,
            )

        if aqi >= 201:
            return (
                "very_unhealthy",
                NotificationSeverity.CRITICAL,
            )

        if aqi >= 151:
            return (
                "unhealthy",
                NotificationSeverity.WARNING,
            )

        if aqi >= 101:
            return (
                "sensitive_groups",
                NotificationSeverity.CAUTION,
            )

        return None

    @staticmethod
    def _aqi_title(
        band: str,
    ) -> str:
        titles = {
            "hazardous": ("Hazardous air quality"),
            "very_unhealthy": ("Very unhealthy air quality"),
            "unhealthy": ("Unhealthy air quality"),
            "sensitive_groups": ("Air quality may affect sensitive groups"),
        }

        return titles.get(
            band,
            "Air quality alert",
        )

    @staticmethod
    def _aqi_message(
        *,
        aqi: int,
        band: str,
    ) -> str:
        if band == "hazardous":
            return (
                f"Current AQI is {aqi}. "
                "Avoid unnecessary outdoor "
                "activity where possible."
            )

        if band == "very_unhealthy":
            return f"Current AQI is {aqi}. Consider reducing outdoor activity."

        if band == "unhealthy":
            return (
                f"Current AQI is {aqi}. Prolonged outdoor activity may be unsuitable."
            )

        return (
            f"Current AQI is {aqi}. "
            "Sensitive individuals should "
            "consider limiting prolonged "
            "outdoor activity."
        )

    @staticmethod
    def _daily_item_for_date(
        *,
        context: WeatherContextResponse,
        target_date: date,
    ):
        target = target_date.isoformat()

        for item in context.daily:
            item_date = (
                item.date.isoformat()
                if isinstance(
                    item.date,
                    date,
                )
                else str(item.date)
            )

            if item_date == target:
                return item

        return None

    async def evaluate_environmental_conditions(
        self,
        *,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
        context: WeatherContextResponse,
        target_date: date,
    ) -> int:
        """
        Evaluate AQI and rain conditions for the
        current homepage location.

        These notifications are independent of
        My Day routines.
        """

        preference = await self.preference_repository.get_preference(user_id)

        if preference is None:
            return 0

        # Avoid generating notifications when somebody
        # requests a historical/future homepage date.
        #
        # Environmental notifications should represent
        # current conditions.
        observed_at = context.current.observed_at

        if observed_at is not None and observed_at.date() != target_date:
            return 0

        created_count = 0

        # -------------------------------------------------
        # AQI notification
        # -------------------------------------------------

        if preference.aqi_alerts_enabled and context.air_quality is not None:
            raw_aqi = (
                context.air_quality.us_aqi
                if context.air_quality.us_aqi is not None
                else context.air_quality.aqi
            )

            if raw_aqi is not None:
                aqi = round(raw_aqi)

                band_result = self._aqi_band(aqi)

                if band_result is not None:
                    (
                        band,
                        severity,
                    ) = band_result

                    (
                        _,
                        created,
                    ) = await self.notification_service.create_notification_once(
                        user_id=user_id,
                        notification_type=(NotificationType.AQI_ALERT),
                        title=(self._aqi_title(band)),
                        message=(
                            self._aqi_message(
                                aqi=aqi,
                                band=band,
                            )
                        ),
                        severity=severity,
                        source=("open_meteo_air_quality"),
                        related_location_id=(location_id),
                        source_reference=(
                            f"aqi:{location_id}:{target_date.isoformat()}:{band}"
                        ),
                    )

                    if created:
                        created_count += 1

        # -------------------------------------------------
        # Rain notification
        # -------------------------------------------------

        if preference.rain_alerts_enabled:
            today = self._daily_item_for_date(
                context=context,
                target_date=target_date,
            )

            current_rain = context.current.rain or 0

            probability = today.rain_probability_max if today is not None else None

            rain_expected = current_rain > 0 or (
                probability is not None and probability >= 70
            )

            if rain_expected:
                if current_rain > 0:
                    title = "Rain detected"

                    message = "Rain is currently being recorded at your saved location."

                else:
                    title = "High chance of rain"

                    message = f"There is a {probability}% chance of rain today."

                severity = (
                    NotificationSeverity.WARNING
                    if (
                        current_rain >= 5
                        or (probability is not None and probability >= 90)
                    )
                    else NotificationSeverity.CAUTION
                )

                _, created = await self.notification_service.create_notification_once(
                    user_id=user_id,
                    notification_type=(NotificationType.RAIN_ALERT),
                    title=title,
                    message=message,
                    severity=severity,
                    source="open_meteo",
                    related_location_id=(location_id),
                    source_reference=(f"rain:{location_id}:{target_date.isoformat()}"),
                )

                if created:
                    created_count += 1

        return created_count

    async def evaluate_daily_summary(
        self,
        *,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
        context: WeatherContextResponse,
        my_day: MyDayResponse,
        target_date: date,
    ) -> int:
        """
        Create one daily weather summary notification
        per user/location/date.

        This is currently generated during homepage refresh.
        Later FCM/background scheduling can generate it
        automatically in the morning.
        """

        preference = await self.preference_repository.get_preference(user_id)

        if preference is None:
            return 0

        if not preference.daily_summary_enabled:
            return 0

        observed_at = context.current.observed_at

        # Do not create summaries when viewing another date.
        if observed_at is not None and observed_at.date() != target_date:
            return 0

        current_temperature = context.current.temperature

        aqi: int | None = None

        if context.air_quality is not None:
            raw_aqi = (
                context.air_quality.us_aqi
                if context.air_quality.us_aqi is not None
                else context.air_quality.aqi
            )

            if raw_aqi is not None:
                aqi = round(raw_aqi)

        today = self._daily_item_for_date(
            context=context,
            target_date=target_date,
        )

        rain_probability = today.rain_probability_max if today is not None else None

        caution_count = sum(
            1
            for routine in my_day.routines
            if routine.impact == RoutineImpactLevel.CAUTION
        )

        avoid_count = sum(
            1
            for routine in my_day.routines
            if routine.impact == RoutineImpactLevel.AVOID
        )

        parts: list[str] = []

        if current_temperature is not None:
            parts.append(f"Current temperature is {current_temperature:.1f}°C.")

        if aqi is not None:
            parts.append(f"US AQI is {aqi}.")

        if rain_probability is not None:
            parts.append(f"Today's maximum rain probability is {rain_probability}%.")

        if avoid_count > 0:
            parts.append(
                f"{avoid_count} planned "
                f"{'routine is' if avoid_count == 1 else 'routines are'} "
                f"recommended to be avoided."
            )

        if caution_count > 0:
            parts.append(
                f"{caution_count} planned "
                f"{'routine needs' if caution_count == 1 else 'routines need'} "
                f"caution."
            )

        if not parts:
            parts.append("Your weather summary is ready.")

        _, created = await self.notification_service.create_notification_once(
            user_id=user_id,
            notification_type=(NotificationType.DAILY_SUMMARY),
            title="Today's weather summary",
            message=" ".join(parts),
            severity=(NotificationSeverity.INFO),
            source="mausam",
            related_location_id=location_id,
            source_reference=(f"daily_summary:{location_id}:{target_date.isoformat()}"),
        )

        return 1 if created else 0
