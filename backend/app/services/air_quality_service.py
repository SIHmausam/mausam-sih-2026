from typing import Any

from redis.asyncio import Redis

from app.integrations.air_quality.base import (
    AirQualityProvider,
)
from app.schemas.air_quality import (
    CurrentAirQualityResponse,
    HourlyAirQualityItem,
    HourlyAirQualityResponse,
)


class AirQualityService:
    CURRENT_TTL = 1800
    HOURLY_TTL = 3600

    def __init__(
        self,
        provider: AirQualityProvider,
        redis: Redis,
    ):
        self.provider = provider
        self.redis = redis

    @staticmethod
    def _coordinate_key(
        latitude: float,
        longitude: float,
    ) -> str:
        return f"{latitude:.3f}:{longitude:.3f}"

    @staticmethod
    def _value_at(
        values: list[Any] | None,
        index: int,
    ) -> Any | None:
        if not values:
            return None

        if index >= len(values):
            return None

        return values[index]

    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> CurrentAirQualityResponse:
        coordinates = self._coordinate_key(
            latitude,
            longitude,
        )

        cache_key = f"air_quality:current:{coordinates}"

        cached = await self.redis.get(cache_key)

        if cached:
            return CurrentAirQualityResponse.model_validate_json(cached)

        raw = await self.provider.get_current(
            latitude,
            longitude,
        )

        current = raw.get(
            "current",
            {},
        )

        us_aqi = current.get("us_aqi")

        european_aqi = current.get("european_aqi")

        if us_aqi is not None:
            normalized_aqi = us_aqi
            aqi_standard = "us"
        elif european_aqi is not None:
            normalized_aqi = european_aqi
            aqi_standard = "european"
        else:
            normalized_aqi = None
            aqi_standard = None

        response = CurrentAirQualityResponse(
            latitude=latitude,
            longitude=longitude,
            aqi=normalized_aqi,
            aqi_standard=aqi_standard,
            us_aqi=us_aqi,
            european_aqi=european_aqi,
            pm2_5=current.get("pm2_5"),
            pm10=current.get("pm10"),
            nitrogen_dioxide=current.get("nitrogen_dioxide"),
            sulphur_dioxide=current.get("sulphur_dioxide"),
            carbon_monoxide=current.get("carbon_monoxide"),
            ozone=current.get("ozone"),
            uv_index=current.get("uv_index"),
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=self.CURRENT_TTL,
        )

        return response

    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
    ) -> HourlyAirQualityResponse:
        coordinates = self._coordinate_key(
            latitude,
            longitude,
        )

        cache_key = f"air_quality:hourly:{coordinates}"

        cached = await self.redis.get(cache_key)

        if cached:
            return HourlyAirQualityResponse.model_validate_json(cached)

        raw = await self.provider.get_hourly(
            latitude,
            longitude,
        )

        hourly = raw.get(
            "hourly",
            {},
        )

        times = hourly.get(
            "time",
            [],
        )

        items: list[HourlyAirQualityItem] = []

        for index, time in enumerate(times):
            items.append(
                HourlyAirQualityItem(
                    time=time,
                    us_aqi=self._value_at(
                        hourly.get("us_aqi"),
                        index,
                    ),
                    european_aqi=self._value_at(
                        hourly.get("european_aqi"),
                        index,
                    ),
                    pm2_5=self._value_at(
                        hourly.get("pm2_5"),
                        index,
                    ),
                    pm10=self._value_at(
                        hourly.get("pm10"),
                        index,
                    ),
                    nitrogen_dioxide=self._value_at(
                        hourly.get("nitrogen_dioxide"),
                        index,
                    ),
                    sulphur_dioxide=self._value_at(
                        hourly.get("sulphur_dioxide"),
                        index,
                    ),
                    carbon_monoxide=self._value_at(
                        hourly.get("carbon_monoxide"),
                        index,
                    ),
                    ozone=self._value_at(
                        hourly.get("ozone"),
                        index,
                    ),
                    uv_index=self._value_at(
                        hourly.get("uv_index"),
                        index,
                    ),
                )
            )

        response = HourlyAirQualityResponse(
            latitude=latitude,
            longitude=longitude,
            hourly=items,
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=self.HOURLY_TTL,
        )

        return response
