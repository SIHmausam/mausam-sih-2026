import asyncio
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.weather.base import WeatherProvider


class OpenMeteoWeatherProvider(WeatherProvider):
    def __init__(self) -> None:
        self.base_url = settings.open_meteo_weather_url

        self._forecast_cache: dict[
            tuple[float, float],
            dict[str, Any],
        ] = {}

        self._forecast_tasks: dict[
            tuple[float, float],
            asyncio.Task[dict[str, Any]],
        ] = {}

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

                    # Don't make the user wait forever
                    # for an external provider.
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
            "Open-Meteo weather request failed"
        )

    async def _get_forecast_bundle(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        key = (
            round(latitude, 6),
            round(longitude, 6),
        )

        cached = self._forecast_cache.get(key)

        if cached is not None:
            return cached

        task = self._forecast_tasks.get(key)

        if task is None:
            task = asyncio.create_task(
                self._request(
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
                        "hourly": (
                            "temperature_2m,"
                            "relative_humidity_2m,"
                            "apparent_temperature,"
                            "precipitation,"
                            "rain,"
                            "precipitation_probability,"
                            "weather_code,"
                            "wind_speed_10m,"
                            "visibility,"
                            "soil_moisture_0_to_7cm,"
                            "et0_fao_evapotranspiration,"
                            "vapour_pressure_deficit"
                        ),
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
                        "forecast_hours": 72,
                        "forecast_days": 7,
                        "timezone": "auto",
                    }
                )
            )

            self._forecast_tasks[key] = task

        try:
            result = await task

            self._forecast_cache[key] = result

            return result

        finally:
            if self._forecast_tasks.get(key) is task:
                self._forecast_tasks.pop(
                    key,
                    None,
                )

    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._get_forecast_bundle(
            latitude,
            longitude,
        )

    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._get_forecast_bundle(
            latitude,
            longitude,
        )

    async def get_daily(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._get_forecast_bundle(
            latitude,
            longitude,
        )

    async def get_agriculture_context(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._get_forecast_bundle(
            latitude,
            longitude,
        )
