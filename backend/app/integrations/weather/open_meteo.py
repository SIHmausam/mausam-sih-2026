import asyncio
import logging
from time import perf_counter
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.weather.base import WeatherProvider

logger = logging.getLogger(__name__)

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
        *,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        max_attempts = 3

        request_url = (
            base_url
            or self.base_url
        )

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            for attempt in range(
                1,
                max_attempts + 1,
            ):
                started_at = perf_counter()

                try:
                    response = await client.get(
                        request_url,
                        params=params,
                    )

                except httpx.RequestError as exc:
                    elapsed_ms = (
                        perf_counter()
                        - started_at
                    ) * 1000

                    logger.warning(
                        (
                            "Open-Meteo weather request failed "
                            "attempt=%s/%s error=%s "
                            "duration_ms=%.2f"
                        ),
                        attempt,
                        max_attempts,
                        type(exc).__name__,
                        elapsed_ms,
                    )

                    if attempt == max_attempts:
                        raise

                    await asyncio.sleep(
                        2 ** (attempt - 1)
                    )
                    continue

                elapsed_ms = (
                    perf_counter()
                    - started_at
                ) * 1000

                if response.status_code == 429:
                    logger.warning(
                        (
                            "Open-Meteo weather rate limited "
                            "attempt=%s/%s duration_ms=%.2f"
                        ),
                        attempt,
                        max_attempts,
                        elapsed_ms,
                    )

                    if attempt == max_attempts:
                        response.raise_for_status()

                    retry_after = (
                        response.headers.get(
                            "Retry-After"
                        )
                    )

                    try:
                        delay = (
                            float(retry_after)
                            if retry_after
                            is not None
                            else float(
                                2 ** (attempt - 1)
                            )
                        )
                    except ValueError:
                        delay = float(
                            2 ** (attempt - 1)
                        )

                    await asyncio.sleep(
                        min(delay, 5.0)
                    )
                    continue

                if response.status_code in {
                    500,
                    502,
                    503,
                    504,
                }:
                    logger.warning(
                        (
                            "Open-Meteo weather server error "
                            "status=%s attempt=%s/%s "
                            "duration_ms=%.2f"
                        ),
                        response.status_code,
                        attempt,
                        max_attempts,
                        elapsed_ms,
                    )

                    if attempt == max_attempts:
                        response.raise_for_status()

                    await asyncio.sleep(
                        2 ** (attempt - 1)
                    )
                    continue

                response.raise_for_status()

                logger.debug(
                    (
                        "Open-Meteo weather request succeeded "
                        "status=%s attempt=%s "
                        "duration_ms=%.2f"
                    ),
                    response.status_code,
                    attempt,
                    elapsed_ms,
                )

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
                            "dew_point_2m,"
                            "apparent_temperature,"
                            "precipitation,"
                            "rain,"
                            "showers,"
                            "precipitation_probability,"
                            "weather_code,"
                            "cloud_cover,"
                            "wind_speed_10m,"
                            "wind_direction_10m,"
                            "wind_gusts_10m,"
                            "visibility,"
                            "is_day"
                        ),
                        "hourly": (
                            "temperature_2m,"
                            "relative_humidity_2m,"
                            "dew_point_2m,"
                            "apparent_temperature,"
                            "precipitation,"
                            "rain,"
                            "showers,"
                            "precipitation_probability,"
                            "weather_code,"
                            "cloud_cover,"
                            "wind_speed_10m,"
                            "wind_direction_10m,"
                            "wind_gusts_10m,"
                            "visibility,"

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
                            "precipitation_hours,"
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
        # Generic forecast supplies ET0 and VPD.
        forecast_task = asyncio.create_task(
            self._get_forecast_bundle(
                latitude,
                longitude,
            )
        )

        # ECMWF supplies the exact soil depth bands used
        # by the Phase 2 personalization model.
        soil_task = asyncio.create_task(
            self._request(
                {
                    "latitude": latitude,
                    "longitude": longitude,

                    # IMPORTANT:
                    # Pass this as a list, not a
                    # comma-separated string.
                    "hourly": [
                        "soil_moisture_0_to_7cm",
                        "soil_moisture_7_to_28cm",
                        "soil_moisture_28_to_100cm",
                        "soil_moisture_100_to_255cm",
                        "soil_temperature_0_to_7cm",
                        "soil_temperature_7_to_28cm",
                        "soil_temperature_28_to_100cm",
                        "soil_temperature_100_to_255cm",
                    ],

                    "forecast_hours": 48,
                    "timezone": "auto",
                },
                base_url=(
                    settings.open_meteo_ecmwf_url
                ),
            )
        )

        forecast_raw, soil_raw = await asyncio.gather(
            forecast_task,
            soil_task,
        )

        forecast_hourly = forecast_raw.get(
            "hourly",
            {},
        )

        soil_hourly = soil_raw.get(
            "hourly",
            {},
        )

        return {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": {
                **forecast_hourly,
                **soil_hourly,
            },
        }
