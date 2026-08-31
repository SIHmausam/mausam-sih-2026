import asyncio

from app.schemas.weather import WeatherContextResponse
from app.services.air_quality_service import (
    AirQualityService,
)
from app.services.weather_service import WeatherService


class WeatherContextService:
    def __init__(
        self,
        weather_service: WeatherService,
        air_quality_service: AirQualityService,
    ):
        self.weather_service = weather_service
        self.air_quality_service = air_quality_service

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
        )

        return WeatherContextResponse(
            latitude=latitude,
            longitude=longitude,
            current=current,
            hourly=hourly.hourly,
            daily=daily.daily,
            agriculture=agriculture,
            air_quality=air_quality,
        )
