import asyncio
import uuid
from datetime import (
    UTC,
    date,
    datetime,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.personalization.base import (
    PersonalizationProvider,
)
from app.integrations.push.base import (
    PushProvider,
)
from app.models.saved_location import SavedLocation
from app.repositories.location_repository import (
    LocationRepository,
)
from app.schemas.alert import OfficialAlert
from app.schemas.homepage import (
    HomepageLocation,
    HomepageResponse,
    HomepageWeatherSummary,
)
from app.schemas.weather import (
    DailyWeatherItem,
    WeatherContextResponse,
)
from app.services.alert_service import AlertService
from app.services.my_day_service import MyDayService
from app.services.notification_evaluation_service import (
    NotificationEvaluationService,
)
from app.services.personalization_service import (
    PersonalizationService,
)
from app.services.weather_context_service import (
    WeatherContextService,
)


class HomepageLocationNotFoundError(Exception):
    pass


class HomepageService:
    def __init__(
        self,
        session: AsyncSession,
        weather_context_service: WeatherContextService,
        alert_service: AlertService,
        personalization_provider: PersonalizationProvider,
        push_provider: PushProvider | None = None,
    ):
        self.location_repository = LocationRepository(session)

        self.weather_context_service = weather_context_service

        self.alert_service = alert_service

        self.my_day_service = MyDayService(
            session=session,
            weather_context_service=(weather_context_service),
            alert_service=alert_service,
        )

        self.personalization_service = PersonalizationService(
            session=session,
            weather_context_service=(weather_context_service),
            personalization_provider=(personalization_provider),
        )

        self.notification_evaluation_service = NotificationEvaluationService(
            session=session,
            push_provider=push_provider,
        )

    async def _resolve_location(
        self,
        *,
        user_id: uuid.UUID,
        location_id: uuid.UUID | None,
    ) -> SavedLocation:
        """
        Resolve the location used by the homepage.

        If location_id is supplied, the location must
        belong to the authenticated user.

        Otherwise, use the user's primary location.
        """

        if location_id is not None:
            location = await self.location_repository.get_owned_location(
                location_id=location_id,
                user_id=user_id,
            )

            if location is None:
                raise HomepageLocationNotFoundError("Saved location not found")

            return location

        location = await self.location_repository.get_primary_for_user(user_id=user_id)

        if location is None:
            raise HomepageLocationNotFoundError("Primary saved location not found")

        return location

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:
        """
        Normalize datetime values to UTC.

        Provider values that are currently timezone-naive
        are treated as UTC for defensive comparison.
        """

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    @classmethod
    def _is_active_alert(
        cls,
        alert: OfficialAlert,
        now: datetime,
    ) -> bool:
        """
        Defensive homepage-level active-alert check.

        AlertService should already remove inactive alerts,
        but keeping this here prevents stale safety data from
        reaching the homepage if that behavior changes later.
        """

        start = alert.onset_at or alert.effective_at

        if start is not None:
            normalized_start = cls._normalize_datetime(start)

            if normalized_start > now:
                return False

        if alert.expires_at is not None:
            normalized_expiry = cls._normalize_datetime(alert.expires_at)

            if normalized_expiry < now:
                return False

        return True

    @staticmethod
    def _severity_priority(
        alert: OfficialAlert,
    ) -> int:
        """
        Smaller number means greater safety priority.
        """

        priorities = {
            "extreme": 0,
            "severe": 1,
            "moderate": 2,
            "minor": 3,
        }

        severity = (alert.severity or "").casefold()

        return priorities.get(
            severity,
            4,
        )

    @staticmethod
    def _has_safety_override(
        alerts: list[OfficialAlert],
    ) -> bool:
        """
        Severe and Extreme official alerts always
        override personalization.
        """

        return any(
            (alert.severity or "").casefold()
            in {
                "severe",
                "extreme",
            }
            for alert in alerts
        )

    @staticmethod
    def _deduplicate_alerts(
        alerts: list[OfficialAlert],
    ) -> list[OfficialAlert]:
        """
        One CAP alert may apply to several saved locations.

        Return every unique official alert only once.
        """

        unique: dict[
            str,
            OfficialAlert,
        ] = {}

        for alert in alerts:
            unique[alert.identifier] = alert

        return list(unique.values())

    @staticmethod
    def _find_today(
        *,
        context: WeatherContextResponse,
        target_date: date,
    ) -> DailyWeatherItem | None:
        """
        Return the daily forecast for target_date.
        """

        target = target_date.isoformat()

        for item in context.daily:
            if item.date == target:
                return item

        # Provider fallback if the exact target
        # date isn't available.
        if context.daily:
            return context.daily[0]

        return None

    async def get_homepage(
        self,
        *,
        user_id: uuid.UUID,
        target_date: date,
        location_id: uuid.UUID | None = None,
    ) -> HomepageResponse:
        """
        Build the complete personalized homepage.

        The homepage combines:

        - primary/specified location
        - current weather
        - current AQI
        - agriculture context
        - today's forecast
        - official alerts
        - My Day routine impact
        - ML/fallback card ranking

        Environmental data and official alerts are shared
        with MyDayService to avoid repeating expensive
        provider/SACHET requests.
        """

        location = await self._resolve_location(
            user_id=user_id,
            location_id=location_id,
        )

        # -----------------------------------------------------
        # Phase 1:
        # Fetch environmental context + official alerts once
        # for the homepage location.
        # -----------------------------------------------------

        (
            context,
            homepage_alerts,
        ) = await asyncio.gather(
            self.weather_context_service.get_context(
                latitude=location.latitude,
                longitude=location.longitude,
            ),
            self.alert_service.get_relevant_alerts(
                latitude=location.latitude,
                longitude=location.longitude,
                city=location.city,
            ),
        )

        # -----------------------------------------------------
        # Shared environment cache.
        #
        # MyDayService will reuse this entry for routines at
        # the same physical location rather than fetching
        # weather + alerts again.
        #
        # MyDayService may add additional routine locations
        # into this same dictionary.
        # -----------------------------------------------------

        environment_cache: dict[
            tuple[
                float,
                float,
                str,
            ],
            tuple[
                WeatherContextResponse,
                list[OfficialAlert],
            ],
        ] = {
            MyDayService.environment_key(location): (
                context,
                homepage_alerts,
            )
        }

        # -----------------------------------------------------
        # Phase 2:
        #
        # My Day can reuse the already fetched environment.
        #
        # ML personalization can also reuse the same
        # WeatherContext instead of fetching Open-Meteo again.
        # -----------------------------------------------------

        (
            my_day,
            personalization,
        ) = await asyncio.gather(
            self.my_day_service.get_my_day(
                user_id=user_id,
                target_date=target_date,
                context_cache=(environment_cache),
            ),
            self.personalization_service.personalize_with_context(
                user_id=user_id,
                location=location,
                context=context,
            ),
        )

        # -----------------------------------------------------
        # MyDayService may have fetched additional environments
        # for routines at other physical locations.
        #
        # Pull official alerts from every cached location.
        # No additional SACHET request is required here.
        # -----------------------------------------------------

        combined_alerts = [
            alert
            for (
                _location_context,
                location_alerts,
            ) in environment_cache.values()
            for alert in location_alerts
        ]

        combined_alerts = self._deduplicate_alerts(combined_alerts)

        now = datetime.now(UTC)

        # AlertService should already perform this filtering.
        # Keep the defensive check at homepage level too.
        active_alerts = [
            alert
            for alert in combined_alerts
            if self._is_active_alert(
                alert,
                now,
            )
        ]

        # Extreme → Severe → Moderate → Minor → Unknown.
        active_alerts.sort(key=self._severity_priority)

        await self.notification_evaluation_service.evaluate_official_alerts(
            user_id=user_id,
            location_id=location.id,
            alerts=active_alerts,
        )

        await self.notification_evaluation_service.evaluate_routine_impacts(
            user_id=user_id,
            my_day=my_day,
        )

        await self.notification_evaluation_service.evaluate_environmental_conditions(
            user_id=user_id,
            location_id=location.id,
            context=context,
            target_date=target_date,
        )

        await self.notification_evaluation_service.evaluate_daily_summary(
            user_id=user_id,
            location_id=location.id,
            context=context,
            my_day=my_day,
            target_date=target_date,
        )

        today = self._find_today(
            context=context,
            target_date=target_date,
        )

        # -----------------------------------------------------
        # Final homepage response.
        # -----------------------------------------------------

        return HomepageResponse(
            # Each homepage load gets a new session.
            #
            # React Native sends this back with card
            # interactions.
            session_id=str(uuid.uuid4()),
            generated_at=now,
            location=HomepageLocation(
                id=location.id,
                label=location.label,
                city=location.city,
                latitude=location.latitude,
                longitude=location.longitude,
                location_type=(location.location_type),
            ),
            has_safety_override=(self._has_safety_override(active_alerts)),
            alerts=active_alerts,
            weather=HomepageWeatherSummary(
                current=context.current,
                air_quality=(context.air_quality),
                agriculture=(context.agriculture),
                today=today,
            ),
            my_day=my_day,
            personalization=personalization,
        )
