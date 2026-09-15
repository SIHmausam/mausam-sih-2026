import asyncio
import logging
from time import perf_counter
from typing import Any

import httpx

from app.core.config import settings
from app.core.metrics import (
    PROVIDER_FAILURES,
    PROVIDER_RATE_LIMITS,
    PROVIDER_REQUEST_DURATION,
    PROVIDER_REQUESTS,
    PROVIDER_RETRIES,
)
from app.integrations.air_quality.base import (
    AirQualityProvider,
)

logger = logging.getLogger(__name__)

class OpenMeteoAirQualityProvider(AirQualityProvider):
    def __init__(self) -> None:
        self.base_url = settings.open_meteo_air_quality_url

    async def _request(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        max_attempts = 3
        provider_name = "air_quality"

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
                        self.base_url,
                        params=params,
                    )

                except httpx.RequestError as exc:
                    elapsed_seconds = (
                        perf_counter()
                        - started_at
                    )

                    PROVIDER_REQUESTS.labels(
                        provider=provider_name,
                        outcome="request_error",
                    ).inc()

                    PROVIDER_REQUEST_DURATION.labels(
                        provider=provider_name,
                    ).observe(
                        elapsed_seconds
                    )

                    logger.warning(
                        (
                            "Open-Meteo air-quality request failed "
                            "attempt=%s/%s error=%s "
                            "duration_ms=%.2f"
                        ),
                        attempt,
                        max_attempts,
                        type(exc).__name__,
                        elapsed_seconds * 1000,
                    )

                    if attempt == max_attempts:
                        PROVIDER_FAILURES.labels(
                            provider=provider_name,
                            reason="request_error",
                        ).inc()

                        raise

                    PROVIDER_RETRIES.labels(
                        provider=provider_name,
                        reason="request_error",
                    ).inc()

                    await asyncio.sleep(
                        2 ** (attempt - 1)
                    )

                    continue

                elapsed_seconds = (
                    perf_counter()
                    - started_at
                )

                if response.status_code == 429:
                    PROVIDER_REQUESTS.labels(
                        provider=provider_name,
                        outcome="rate_limited",
                    ).inc()

                    PROVIDER_RATE_LIMITS.labels(
                        provider=provider_name,
                    ).inc()

                    PROVIDER_REQUEST_DURATION.labels(
                        provider=provider_name,
                    ).observe(
                        elapsed_seconds
                    )

                    logger.warning(
                        (
                            "Open-Meteo air-quality rate limited "
                            "attempt=%s/%s "
                            "duration_ms=%.2f"
                        ),
                        attempt,
                        max_attempts,
                        elapsed_seconds * 1000,
                    )

                    if attempt == max_attempts:
                        PROVIDER_FAILURES.labels(
                            provider=provider_name,
                            reason="rate_limited",
                        ).inc()

                        response.raise_for_status()

                    PROVIDER_RETRIES.labels(
                        provider=provider_name,
                        reason="rate_limited",
                    ).inc()

                    retry_after = (
                        response.headers.get(
                            "Retry-After"
                        )
                    )

                    try:
                        delay = (
                            float(retry_after)
                            if retry_after is not None
                            else float(
                                2 ** (attempt - 1)
                            )
                        )
                    except ValueError:
                        delay = float(
                            2 ** (attempt - 1)
                        )

                    delay = min(
                        delay,
                        5.0,
                    )

                    await asyncio.sleep(
                        delay
                    )

                    continue

                if response.status_code in {
                    500,
                    502,
                    503,
                    504,
                }:
                    PROVIDER_REQUESTS.labels(
                        provider=provider_name,
                        outcome="server_error",
                    ).inc()

                    PROVIDER_REQUEST_DURATION.labels(
                        provider=provider_name,
                    ).observe(
                        elapsed_seconds
                    )

                    logger.warning(
                        (
                            "Open-Meteo air-quality server error "
                            "status=%s attempt=%s/%s "
                            "duration_ms=%.2f"
                        ),
                        response.status_code,
                        attempt,
                        max_attempts,
                        elapsed_seconds * 1000,
                    )

                    if attempt == max_attempts:
                        PROVIDER_FAILURES.labels(
                            provider=provider_name,
                            reason="server_error",
                        ).inc()

                        response.raise_for_status()

                    PROVIDER_RETRIES.labels(
                        provider=provider_name,
                        reason="server_error",
                    ).inc()

                    await asyncio.sleep(
                        2 ** (attempt - 1)
                    )

                    continue

                if 400 <= response.status_code < 500:
                    PROVIDER_REQUESTS.labels(
                        provider=provider_name,
                        outcome="client_error",
                    ).inc()

                    PROVIDER_REQUEST_DURATION.labels(
                        provider=provider_name,
                    ).observe(
                        elapsed_seconds
                    )

                    PROVIDER_FAILURES.labels(
                        provider=provider_name,
                        reason="client_error",
                    ).inc()

                    response.raise_for_status()

                response.raise_for_status()

                PROVIDER_REQUESTS.labels(
                    provider=provider_name,
                    outcome="success",
                ).inc()

                PROVIDER_REQUEST_DURATION.labels(
                    provider=provider_name,
                ).observe(
                    elapsed_seconds
                )

                logger.debug(
                    (
                        "Open-Meteo air-quality request succeeded "
                        "status=%s attempt=%s "
                        "duration_ms=%.2f"
                    ),
                    response.status_code,
                    attempt,
                    elapsed_seconds * 1000,
                )

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
                    "uv_index,"
                    "uv_index_clear_sky"
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
                    "uv_index,"
                    "uv_index_clear_sky"
                ),
                "forecast_days": 3,
                "timezone": "auto",
            }
        )
