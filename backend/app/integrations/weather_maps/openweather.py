import asyncio

import httpx

from app.integrations.weather_maps.base import (
    WeatherMapProvider,
    WeatherMapProviderError,
)


class OpenWeatherMapProvider(WeatherMapProvider):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def get_tile(
        self,
        *,
        layer: str,
        zoom: int,
        x: int,
        y: int,
    ) -> bytes:
        url = (
            f"{self.base_url}/{layer}/"
            f"{zoom}/{x}/{y}.png"
        )

        max_attempts = 2

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
        ) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        url,
                        params={"appid": self.api_key},
                    )

                except httpx.RequestError as exc:
                    if attempt == max_attempts - 1:
                        raise WeatherMapProviderError(
                            "Weather map provider is unavailable"
                        ) from exc

                    await asyncio.sleep(0.5)
                    continue

                if response.status_code == 429:
                    raise WeatherMapProviderError(
                        "Weather map provider rate limit reached"
                    )

                if response.status_code in {
                    500,
                    502,
                    503,
                    504,
                }:
                    if attempt == max_attempts - 1:
                        raise WeatherMapProviderError(
                            "Weather map provider is unavailable"
                        )

                    await asyncio.sleep(0.5)
                    continue

                if response.status_code in {401, 403}:
                    raise WeatherMapProviderError(
                        "Weather map provider authentication failed"
                    )

                try:
                    response.raise_for_status()

                except httpx.HTTPStatusError as exc:
                    raise WeatherMapProviderError(
                        "Weather map provider request failed"
                    ) from exc

                content_type = response.headers.get(
                    "content-type",
                    "",
                ).lower()

                if not content_type.startswith("image/"):
                    raise WeatherMapProviderError(
                        "Weather map provider returned "
                        "an invalid tile"
                    )

                return response.content

        raise WeatherMapProviderError(
            "Weather map provider request failed"
        )