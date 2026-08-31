from typing import Any

import httpx

from app.core.config import settings
from app.integrations.air_quality.base import (
    AirQualityProvider,
)


class OpenMeteoAirQualityProvider(AirQualityProvider):
    def __init__(self) -> None:
        self.base_url = settings.open_meteo_air_quality_url

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
                    "us_aqi,"
                    "european_aqi,"
                    "pm2_5,"
                    "pm10,"
                    "nitrogen_dioxide,"
                    "sulphur_dioxide,"
                    "carbon_monoxide,"
                    "ozone,"
                    "uv_index"
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
                    "us_aqi,"
                    "european_aqi,"
                    "pm2_5,"
                    "pm10,"
                    "nitrogen_dioxide,"
                    "sulphur_dioxide,"
                    "carbon_monoxide,"
                    "ozone,"
                    "uv_index"
                ),
                "forecast_days": 3,
                "timezone": "auto",
            }
        )
