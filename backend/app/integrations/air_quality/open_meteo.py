import asyncio
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
        max_attempts = 3

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        self.base_url,
                        params=params,
                    )
                except httpx.RequestError:
                    if attempt == max_attempts - 1:
                        raise

                    await asyncio.sleep(2**attempt)
                    continue

                if response.status_code == 429:
                    if attempt == max_attempts - 1:
                        response.raise_for_status()

                    retry_after = response.headers.get(
                        "Retry-After"
                    )

                    try:
                        delay = (
                            float(retry_after)
                            if retry_after is not None
                            else float(2**attempt)
                        )
                    except ValueError:
                        delay = float(2**attempt)

                    delay = min(delay, 5.0)

                    await asyncio.sleep(delay)
                    continue

                if response.status_code in {
                    500,
                    502,
                    503,
                    504,
                }:
                    if attempt == max_attempts - 1:
                        response.raise_for_status()

                    await asyncio.sleep(2**attempt)
                    continue

                response.raise_for_status()

                return response.json()

        raise RuntimeError(
            "Open-Meteo air-quality request failed"
        )

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
