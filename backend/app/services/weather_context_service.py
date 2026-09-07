import asyncio
import logging

import httpx

from app.schemas.weather import (
    CurrentWeatherResponse,
    WeatherContextResponse,
)
from app.services.air_quality_service import (
    AirQualityService,
)
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class WeatherContextService:
    def __init__(
        self,
        weather_service: WeatherService,
        air_quality_service: AirQualityService,
    ):
        self.weather_service = weather_service
        self.air_quality_service = air_quality_service

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
        try:
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

            )

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429:
                raise

            logger.warning(
                "Weather provider rate limited request for latitude=%s longitude=%s",
                latitude,
                longitude,
            )

            return self._unavailable_context(
                latitude=latitude,
                longitude=longitude,
                message=(
                    "Weather data is temporarily unavailable. Please try again shortly."
                ),
            )

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
            hourly_air_quality=hourly_air_quality.hourly,
        )
