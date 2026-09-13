import base64
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar

from redis.asyncio import Redis

from app.integrations.weather_maps.base import (
    WeatherMapProvider,
)
from app.schemas.weather_map import (
    WeatherMapConfigResponse,
    WeatherMapLayer,
    WeatherMapLayerResponse,
)


class WeatherMapTileValidationError(ValueError):
    pass


class WeatherMapRateLimitError(RuntimeError):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class WeatherMapLayerDefinition:
    provider_layer: str
    label: str
    opacity: float


@dataclass(
    frozen=True,
    slots=True,
)
class WeatherMapTileResult:
    content: bytes
    cache_hit: bool


class WeatherMapService:
    LAYERS: ClassVar[
    dict[
        WeatherMapLayer,
        WeatherMapLayerDefinition,
    ]
] = {
        "precipitation": WeatherMapLayerDefinition(
            provider_layer="precipitation_new",
            label="Precipitation",
            opacity=0.65,
        ),
        "temperature": WeatherMapLayerDefinition(
            provider_layer="temp_new",
            label="Temperature",
            opacity=0.65,
        ),
        "wind": WeatherMapLayerDefinition(
            provider_layer="wind_new",
            label="Wind",
            opacity=0.65,
        ),
        "clouds": WeatherMapLayerDefinition(
            provider_layer="clouds_new",
            label="Clouds",
            opacity=0.60,
        ),
    }

    def __init__(
        self,
        *,
        provider: WeatherMapProvider,
        redis: Redis,
        cache_ttl_seconds: int,
        max_zoom: int,
        provider_requests_per_minute: int,
        user_requests_per_minute: int,
    ) -> None:
        self.provider = provider
        self.redis = redis

        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_zoom = max_zoom

        self.provider_requests_per_minute = (
            provider_requests_per_minute
        )

        self.user_requests_per_minute = (
            user_requests_per_minute
        )

    def get_config(
        self,
    ) -> WeatherMapConfigResponse:
        return WeatherMapConfigResponse(
            default_layer="precipitation",

            tile_url_template=(
                "/api/v1/weather/maps/tiles/"
                "{layer}/{z}/{x}/{y}"
            ),

            min_zoom=0,
            max_zoom=self.max_zoom,

            cache_ttl_seconds=(
                self.cache_ttl_seconds
            ),

            attribution=(
                "Weather data © OpenWeather"
            ),

            layers=[
                WeatherMapLayerResponse(
                    id=layer,
                    label=definition.label,
                    opacity=definition.opacity,
                )
                for layer, definition
                in self.LAYERS.items()
            ],
        )

    async def get_tile(
        self,
        *,
        user_id: uuid.UUID,
        layer: WeatherMapLayer,
        zoom: int,
        x: int,
        y: int,
    ) -> WeatherMapTileResult:

        self._validate_tile_coordinates(
            zoom=zoom,
            x=x,
            y=y,
        )

        await self._check_user_rate_limit(
            user_id
        )

        definition = self.LAYERS[layer]

        cache_key = (
            "weather-map:tile:v1:"
            f"{definition.provider_layer}:"
            f"{zoom}:{x}:{y}"
        )

        cached = await self.redis.get(
            cache_key
        )

        if cached is not None:
            encoded = (
                cached.decode("ascii")
                if isinstance(cached, bytes)
                else cached
            )

            return WeatherMapTileResult(
                content=base64.b64decode(
                    encoded
                ),
                cache_hit=True,
            )

        await self._check_provider_rate_limit()

        content = await self.provider.get_tile(
            layer=definition.provider_layer,
            zoom=zoom,
            x=x,
            y=y,
        )

        encoded_content = (
            base64.b64encode(content)
            .decode("ascii")
        )

        await self.redis.set(
            cache_key,
            encoded_content,
            ex=self.cache_ttl_seconds,
        )

        return WeatherMapTileResult(
            content=content,
            cache_hit=False,
        )

    def _validate_tile_coordinates(
        self,
        *,
        zoom: int,
        x: int,
        y: int,
    ) -> None:

        if zoom < 0 or zoom > self.max_zoom:
            raise WeatherMapTileValidationError(
                f"Zoom must be between "
                f"0 and {self.max_zoom}"
            )

        tile_limit = 2**zoom

        if (
            not 0 <= x < tile_limit
            or not 0 <= y < tile_limit
        ):
            raise WeatherMapTileValidationError(
                "Invalid x/y coordinates "
                "for this zoom level"
            )

    async def _check_user_rate_limit(
        self,
        user_id: uuid.UUID,
    ) -> None:

        bucket = datetime.now(
            UTC
        ).strftime("%Y%m%d%H%M")

        key = (
            f"weather-map:user:"
            f"{user_id}:{bucket}"
        )

        count = await self.redis.incr(key)

        if count == 1:
            await self.redis.expire(
                key,
                70,
            )

        if (
            count
            > self.user_requests_per_minute
        ):
            raise WeatherMapRateLimitError(
                "Weather map request "
                "limit exceeded"
            )

    async def _check_provider_rate_limit(
        self,
    ) -> None:

        bucket = datetime.now(
            UTC
        ).strftime("%Y%m%d%H%M")

        key = (
            f"weather-map:provider:"
            f"{bucket}"
        )

        count = await self.redis.incr(key)

        if count == 1:
            await self.redis.expire(
                key,
                70,
            )

        if (
            count
            > self.provider_requests_per_minute
        ):
            raise WeatherMapRateLimitError(
                "Weather map provider budget "
                "temporarily exhausted"
            )