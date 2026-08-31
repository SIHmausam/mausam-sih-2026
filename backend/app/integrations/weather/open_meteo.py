from typing import Any

import httpx

from app.core.config import settings
from app.integrations.weather.base import WeatherProvider


class OpenMeteoWeatherProvider(WeatherProvider):
    def __init__(self) -> None:
        self.base_url = settings.open_meteo_weather_url

    async def _request(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                self.base_url,
                params=params,
            )

            response.raise_for_status()

            return response.json()

    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._request(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "rain,"
                    "weather_code,"
                    "wind_speed_10m,"
                    "is_day"
                ),
                "timezone": "auto",
            }
        )

    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._request(
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "rain,"
                    "precipitation_probability,"
                    "weather_code,"
                    "wind_speed_10m,"
                    "visibility"
                ),
                "forecast_days": 3,
                "timezone": "auto",
            }
        )

    async def get_daily(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._request(
            {
                "latitude": latitude,
                "longitude": longitude,
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "apparent_temperature_max,"
                    "apparent_temperature_min,"
                    "sunrise,"
                    "sunset,"
                    "precipitation_sum,"
                    "rain_sum,"
                    "precipitation_probability_max,"
                    "wind_speed_10m_max"
                ),
                "forecast_days": 7,
                "timezone": "auto",
            }
        )

    async def get_agriculture_context(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._request(
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": (
                    "soil_moisture_0_to_7cm,"
                    "et0_fao_evapotranspiration,"
                    "vapour_pressure_deficit"
                ),
                "forecast_days": 3,
                "timezone": "auto",
            }
        )
