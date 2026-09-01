import uuid
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    ActivityContext,
    RoutineImpactLevel,
)
from app.repositories.location_repository import (
    LocationRepository,
)
from app.repositories.routine_repository import (
    RoutineRepository,
)
from app.schemas.routine import (
    MyDayResponse,
    MyDayRoutineItem,
    RoutineLocationSummary,
    RoutineWeatherSnapshot,
)
from app.services.alert_service import AlertService
from app.services.routine_impact_service import (
    RoutineImpactService,
)
from app.services.weather_context_service import (
    WeatherContextService,
)


class MyDayService:
    def __init__(
        self,
        session: AsyncSession,
        weather_context_service: WeatherContextService,
        alert_service: AlertService,
    ):
        self.routine_repository = RoutineRepository(session)

        self.location_repository = LocationRepository(session)

        self.weather_context_service = weather_context_service

        self.alert_service = alert_service

        self.impact_service = RoutineImpactService()

    @staticmethod
    def _weekday_name(
        target_date: date,
    ) -> str:
        return target_date.strftime("%A").casefold()

    @staticmethod
    def _find_hourly_weather(
        hourly,
        target_date: date,
        start_time,
    ):
        if not hourly:
            return None

        target = datetime.combine(
            target_date,
            start_time,
        )

        return min(
            hourly,
            key=lambda item: abs(item.time.replace(tzinfo=None) - target),
        )

    async def _resolve_location(
        self,
        user_id: uuid.UUID,
        saved_location_id: uuid.UUID | None,
    ):
        if saved_location_id is not None:
            location = await self.location_repository.get_owned_location(
                location_id=saved_location_id,
                user_id=user_id,
            )

            if location is not None:
                return location

        return await self.location_repository.get_primary_for_user(user_id=user_id)

    async def get_my_day(
        self,
        user_id: uuid.UUID,
        target_date: date,
    ) -> MyDayResponse:
        routines = await self.routine_repository.list_enabled_for_user(user_id=user_id)

        weekday = self._weekday_name(target_date)

        todays_routines = [
            routine for routine in routines if weekday in routine.days_of_week
        ]

        results: list[MyDayRoutineItem] = []

        # Avoid rebuilding identical context multiple times
        # when several routines share a saved location.
        context_cache: dict[
            uuid.UUID,
            tuple,
        ] = {}

        for routine in todays_routines:
            location = await self._resolve_location(
                user_id=user_id,
                saved_location_id=(routine.saved_location_id),
            )

            if location is None:
                results.append(
                    MyDayRoutineItem(
                        routine_id=routine.id,
                        name=routine.name,
                        activity_context=(ActivityContext(routine.activity_context)),
                        start_time=routine.start_time,
                        duration_minutes=(routine.duration_minutes),
                        location=None,
                        impact=(RoutineImpactLevel.UNAVAILABLE),
                        reasons=[
                            (
                                "No saved or primary location "
                                "is available for this routine."
                            )
                        ],
                        recommendation=(
                            "Attach a saved location to this "
                            "routine or set a primary location."
                        ),
                        weather=None,
                    )
                )

                continue

            cached = context_cache.get(location.id)

            if cached is None:
                context = await self.weather_context_service.get_context(
                    latitude=location.latitude,
                    longitude=location.longitude,
                )

                alerts = await self.alert_service.get_relevant_alerts(
                    latitude=location.latitude,
                    longitude=location.longitude,
                    city=location.city,
                )

                cached = (
                    context,
                    alerts,
                )

                context_cache[location.id] = cached

            context, alerts = cached

            hourly = self._find_hourly_weather(
                hourly=context.hourly,
                target_date=target_date,
                start_time=routine.start_time,
            )

            weather = RoutineWeatherSnapshot(
                temperature=(
                    hourly.temperature if hourly else context.current.temperature
                ),
                apparent_temperature=(
                    hourly.apparent_temperature
                    if hourly
                    else context.current.apparent_temperature
                ),
                humidity=(hourly.humidity if hourly else context.current.humidity),
                rain=(hourly.rain if hourly else context.current.rain),
                rain_probability=(
                    hourly.rain_probability
                    if hourly
                    else context.current.rain_probability
                ),
                wind_speed=(
                    hourly.wind_speed if hourly else context.current.wind_speed
                ),
                visibility=(
                    hourly.visibility if hourly else context.current.visibility
                ),
                aqi=(context.air_quality.aqi if context.air_quality else None),
                uv_index=(
                    context.air_quality.uv_index if context.air_quality else None
                ),
                surface_soil_moisture=(
                    context.agriculture.surface_soil_moisture
                    if context.agriculture
                    else None
                ),
            )

            activity_context = ActivityContext(routine.activity_context)

            impact = self.impact_service.evaluate(
                activity_context=activity_context,
                weather=weather,
                alerts=alerts,
            )

            results.append(
                MyDayRoutineItem(
                    routine_id=routine.id,
                    name=routine.name,
                    activity_context=(activity_context),
                    start_time=routine.start_time,
                    duration_minutes=(routine.duration_minutes),
                    location=RoutineLocationSummary(
                        id=location.id,
                        label=location.label,
                        city=location.city,
                        latitude=location.latitude,
                        longitude=location.longitude,
                    ),
                    impact=impact.level,
                    reasons=impact.reasons,
                    recommendation=(impact.recommendation),
                    weather=weather,
                )
            )

        return MyDayResponse(
            date=target_date,
            routines=results,
        )
