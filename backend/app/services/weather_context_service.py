import asyncio
import logging

import httpx

from app.schemas.marine import (
    CurrentMarineResponse,
)
from app.schemas.weather import (
    CurrentWeatherResponse,
    WeatherContextResponse,
)
from app.services.air_quality_service import (
    AirQualityService,
)
from app.services.marine_service import (
    MarineService,
)
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class WeatherContextService:
    def __init__(
        self,
        weather_service: WeatherService,
        air_quality_service: AirQualityService,
        marine_service: MarineService | None = None,
    ):
        self.weather_service = weather_service
        self.air_quality_service = air_quality_service
        self.marine_service = marine_service

    @staticmethod
    def _unavailable_context(
        *,
        latitude: float,
        longitude: float,
        message: str,
    ) -> WeatherContextResponse:
        return WeatherContextResponse(
            latitude=latitude,
            longitude=longitude,
            available=False,
            message=message,
            current=CurrentWeatherResponse(
                latitude=latitude,
                longitude=longitude,
            ),
            hourly=[],
            daily=[],
            agriculture=None,
            air_quality=None,
            hourly_air_quality=[],
        )

    async def get_context(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherContextResponse:
        (
            current,
            hourly,
            daily,
            agriculture,
            air_quality,
            hourly_air_quality,
        ) = await asyncio.gather(
            self.weather_service.get_current(
                latitude,
                longitude,
            ),
            self.weather_service.get_hourly(
                latitude,
                longitude,
            ),
            self.weather_service.get_daily(
                latitude,
                longitude,
            ),
            self.weather_service.get_agriculture_context(
                latitude,
                longitude,
            ),
            self.air_quality_service.get_current(
                latitude,
                longitude,
            ),
            self.air_quality_service.get_hourly(
                latitude,
                longitude,
            ),
            return_exceptions=True,
        )

        core_results = (
            ("current", current),
            ("hourly", hourly),
            ("daily", daily),
        )

        for component, result in core_results:
            if isinstance(
                result,
                httpx.HTTPError,
            ):
                logger.warning(
                    (
                        "Core weather provider failed "
                        "component=%s latitude=%s "
                        "longitude=%s error=%s"
                    ),
                    component,
                    latitude,
                    longitude,
                    type(result).__name__,
                )

                return self._unavailable_context(
                    latitude=latitude,
                    longitude=longitude,
                    message=(
                        "Weather data is temporarily "
                        "unavailable. Please try again "
                        "shortly."
                    ),
                )

            # Programming/schema errors should not be silently
            # converted into provider outages.
            if isinstance(
                result,
                Exception,
            ):
                raise result

        if isinstance(
            agriculture,
            httpx.HTTPError,
        ):
            logger.warning(
                (
                    "Agriculture provider unavailable "
                    "latitude=%s longitude=%s error=%s"
                ),
                latitude,
                longitude,
                type(agriculture).__name__,
            )

            agriculture = None

        elif isinstance(
            agriculture,
            Exception,
        ):
            raise agriculture

        if isinstance(
            air_quality,
            httpx.HTTPError,
        ):
            logger.warning(
                (
                    "Current air-quality provider unavailable "
                    "latitude=%s longitude=%s error=%s"
                ),
                latitude,
                longitude,
                type(air_quality).__name__,
            )

            air_quality = None

        elif isinstance(
            air_quality,
            Exception,
        ):
            raise air_quality

        if isinstance(
            hourly_air_quality,
            httpx.HTTPError,
        ):
            logger.warning(
                (
                    "Hourly air-quality provider unavailable "
                    "latitude=%s longitude=%s error=%s"
                ),
                latitude,
                longitude,
                type(hourly_air_quality).__name__,
            )

            hourly_air_quality = None

        elif isinstance(
            hourly_air_quality,
            Exception,
        ):
            raise hourly_air_quality

        return WeatherContextResponse(
            latitude=latitude,
            longitude=longitude,
            available=True,
            message=None,
            current=current,
            hourly=hourly.hourly,
            daily=daily.daily,
            agriculture=agriculture,
            air_quality=air_quality,
            hourly_air_quality=(
                hourly_air_quality.hourly
                if hourly_air_quality
                is not None
                else []
            ),
        )

    async def get_marine_context(
        self,
        latitude: float,
        longitude: float,
    ) -> CurrentMarineResponse | None:
        if self.marine_service is None:
            return None

        try:
            marine = await self.marine_service.get_current(
                latitude,
                longitude,
            )

        except httpx.HTTPError as exc:
            logger.warning(
                (
                    "Marine provider unavailable for "
                    "latitude=%s longitude=%s error=%s"
                ),
                latitude,
                longitude,
                type(exc).__name__,
            )

            return None

        if not marine.available:
            return None

        return marine


    async def attach_marine_context(
        self,
        *,
        context: WeatherContextResponse,
        latitude: float,
        longitude: float,
    ) -> WeatherContextResponse:
        marine = await self.get_marine_context(
            latitude,
            longitude,
        )

        return context.model_copy(
            update={
                "marine": marine,
            }
        )
