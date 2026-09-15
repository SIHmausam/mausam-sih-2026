import asyncio
import logging
from time import perf_counter
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.marine.base import (
    MarineProvider,
)

logger = logging.getLogger(__name__)

class OpenMeteoMarineProvider(
    MarineProvider,
):
    def __init__(self) -> None:
        self.base_url = (
            settings.open_meteo_marine_url
        )

    async def _request(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        max_attempts = 3

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
                    elapsed_ms = (
                        perf_counter()
                        - started_at
                    ) * 1000

                    logger.warning(
                        (
                            "Open-Meteo marine request failed "
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
                            "Open-Meteo marine rate limited "
                            "attempt=%s/%s "
                            "duration_ms=%.2f"
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
                            if retry_after is not None
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
                            "Open-Meteo marine server error "
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
                        "Open-Meteo marine request succeeded "
                        "status=%s attempt=%s "
                        "duration_ms=%.2f"
                    ),
                    response.status_code,
                    attempt,
                    elapsed_ms,
                )

                return response.json()

        raise RuntimeError(
            "Open-Meteo marine request failed"
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
                    "wave_height,"
                    "wave_direction,"
                    "wave_period,"
                    "swell_wave_height,"
                    "swell_wave_direction,"
                    "swell_wave_period,"
                    "sea_level_height_msl,"
                    "sea_surface_temperature"
                ),
                "cell_selection": "sea",
                "timezone": "auto",
            }
        )