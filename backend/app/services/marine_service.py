from math import (
    asin,
    cos,
    radians,
    sin,
    sqrt,
)

from redis.asyncio import Redis

from app.core.config import settings
from app.core.metrics import CACHE_ACCESS
from app.integrations.marine.base import (
    MarineProvider,
)
from app.schemas.marine import (
    CurrentMarineResponse,
)


class MarineService:
    CURRENT_TTL = 600

    def __init__(
        self,
        provider: MarineProvider,
        redis: Redis,
    ):
        self.provider = provider
        self.redis = redis

    @staticmethod
    def _coordinate_key(
        latitude: float,
        longitude: float,
    ) -> str:
        return (
            f"{latitude:.3f}:"
            f"{longitude:.3f}"
        )

    @staticmethod
    def _distance_km(
        latitude_1: float,
        longitude_1: float,
        latitude_2: float,
        longitude_2: float,
    ) -> float:
        earth_radius_km = 6371.0

        lat1 = radians(latitude_1)
        lon1 = radians(longitude_1)

        lat2 = radians(latitude_2)
        lon2 = radians(longitude_2)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        value = (
            sin(delta_lat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2) ** 2
        )

        return (
            2
            * earth_radius_km
            * asin(sqrt(value))
        )

    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> CurrentMarineResponse:
        coordinates = (
            self._coordinate_key(
                latitude,
                longitude,
            )
        )

        cache_key = (
            f"marine:current:v2:"
            f"{coordinates}"
        )

        cached = await self.redis.get(
            cache_key
        )

        if cached:
            CACHE_ACCESS.labels(
                cache="marine_current",
                result="hit",
            ).inc()

            return (
                CurrentMarineResponse
                .model_validate_json(
                    cached
                )
            )

        CACHE_ACCESS.labels(
            cache="marine_current",
            result="miss",
        ).inc()

        raw = await self.provider.get_current(
            latitude,
            longitude,
        )

        current = raw.get(
            "current",
            {},
        )

        provider_latitude = float(
            raw.get(
                "latitude",
                latitude,
            )
        )

        provider_longitude = float(
            raw.get(
                "longitude",
                longitude,
            )
        )

        distance = self._distance_km(
            latitude,
            longitude,
            provider_latitude,
            provider_longitude,
        )

        marine_fields = (
            "wave_height",
            "wave_direction",
            "wave_period",
            "swell_wave_height",
            "swell_wave_direction",
            "swell_wave_period",
            "sea_level_height_msl",
            "sea_surface_temperature",
        )

        has_complete_marine_data = all(
            current.get(field) is not None
            for field in marine_fields
        )

        available = (
            has_complete_marine_data
            and distance
            <= settings.marine_max_grid_distance_km
        )

        response = CurrentMarineResponse(
            latitude=provider_latitude,
            longitude=provider_longitude,

            observed_at=current.get(
                "time"
            ),

            wave_height=current.get(
                "wave_height"
            ),

            wave_direction=current.get(
                "wave_direction"
            ),

            wave_period=current.get(
                "wave_period"
            ),

            swell_wave_height=current.get(
                "swell_wave_height"
            ),

            swell_wave_direction=current.get(
                "swell_wave_direction"
            ),

            swell_wave_period=current.get(
                "swell_wave_period"
            ),

            sea_level_height_msl=(
                current.get(
                    "sea_level_height_msl"
                )
            ),

            sea_surface_temperature=(
                current.get(
                    "sea_surface_temperature"
                )
            ),

            available=available,
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=self.CURRENT_TTL,
        )

        return response