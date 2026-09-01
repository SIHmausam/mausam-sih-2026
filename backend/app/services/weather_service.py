from datetime import datetime
from typing import Any

from redis.asyncio import Redis

from app.integrations.weather.base import WeatherProvider
from app.schemas.weather import (
    AgricultureContextResponse,
    CurrentWeatherResponse,
    DailyWeatherItem,
    DailyWeatherResponse,
    HourlyWeatherItem,
    HourlyWeatherResponse,
)


class WeatherService:
    CURRENT_TTL = 600
    HOURLY_TTL = 1800
    DAILY_TTL = 3600
    AGRICULTURE_TTL = 1800

    def __init__(
        self,
        provider: WeatherProvider,
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
    ) -> CurrentWeatherResponse:
        coordinates = self._coordinate_key(
            latitude,
            longitude,
        )

        cache_key = f"weather:current:{coordinates}"

        cached = await self.redis.get(cache_key)

        if cached:
            return CurrentWeatherResponse.model_validate_json(cached)

        raw = await self.provider.get_current(
            latitude,
            longitude,
        )

        current = raw.get(
            "current",
            {},
        )

        response = CurrentWeatherResponse(
            latitude=latitude,
            longitude=longitude,
            observed_at=current.get("time"),
            temperature=current.get("temperature_2m"),
            apparent_temperature=current.get("apparent_temperature"),
            humidity=current.get("relative_humidity_2m"),
            precipitation=current.get("precipitation"),
            rain=current.get("rain"),
            weather_code=current.get("weather_code"),
            wind_speed=current.get("wind_speed_10m"),
            is_daylight=(
                bool(current.get("is_day"))
                if current.get("is_day") is not None
                else None
            ),
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=self.CURRENT_TTL,
        )

        return response

    @staticmethod
    def _nearest_time_index(
        times: list[Any] | None,
        reference_time: datetime | None,
    ) -> int | None:
        if not times:
            return None

        if reference_time is None:
            return 0

        # Provider timestamps may be timezone-aware or
        # timezone-naive. We compare their wall-clock values
        # consistently here.
        reference = reference_time.replace(tzinfo=None)

        closest_index: int | None = None
        closest_difference: float | None = None

        for index, value in enumerate(times):
            try:
                if isinstance(value, datetime):
                    candidate = value
                else:
                    candidate = datetime.fromisoformat(str(value))
            except ValueError:
                continue

            candidate = candidate.replace(tzinfo=None)

            difference = abs((candidate - reference).total_seconds())

            if closest_difference is None or difference < closest_difference:
                closest_index = index
                closest_difference = difference

        return closest_index

    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
    ) -> HourlyWeatherResponse:
        coordinates = self._coordinate_key(
            latitude,
            longitude,
        )

        cache_key = f"weather:hourly:{coordinates}"

        cached = await self.redis.get(cache_key)

        if cached:
            return HourlyWeatherResponse.model_validate_json(cached)

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

        items: list[HourlyWeatherItem] = []

        for index, time in enumerate(times):
            items.append(
                HourlyWeatherItem(
                    time=time,
                    temperature=self._value_at(
                        hourly.get("temperature_2m"),
                        index,
                    ),
                    apparent_temperature=self._value_at(
                        hourly.get("apparent_temperature"),
                        index,
                    ),
                    humidity=self._value_at(
                        hourly.get("relative_humidity_2m"),
                        index,
                    ),
                    precipitation=self._value_at(
                        hourly.get("precipitation"),
                        index,
                    ),
                    rain=self._value_at(
                        hourly.get("rain"),
                        index,
                    ),
                    rain_probability=self._value_at(
                        hourly.get("precipitation_probability"),
                        index,
                    ),
                    weather_code=self._value_at(
                        hourly.get("weather_code"),
                        index,
                    ),
                    wind_speed=self._value_at(
                        hourly.get("wind_speed_10m"),
                        index,
                    ),
                    visibility=self._value_at(
                        hourly.get("visibility"),
                        index,
                    ),
                )
            )

        response = HourlyWeatherResponse(
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

    async def get_daily(
        self,
        latitude: float,
        longitude: float,
    ) -> DailyWeatherResponse:
        coordinates = self._coordinate_key(
            latitude,
            longitude,
        )

        cache_key = f"weather:daily:{coordinates}"

        cached = await self.redis.get(cache_key)

        if cached:
            return DailyWeatherResponse.model_validate_json(cached)

        raw = await self.provider.get_daily(
            latitude,
            longitude,
        )

        daily = raw.get(
            "daily",
            {},
        )

        dates = daily.get(
            "time",
            [],
        )

        items: list[DailyWeatherItem] = []

        for index, date in enumerate(dates):
            items.append(
                DailyWeatherItem(
                    date=date,
                    weather_code=self._value_at(
                        daily.get("weather_code"),
                        index,
                    ),
                    temperature_max=self._value_at(
                        daily.get("temperature_2m_max"),
                        index,
                    ),
                    temperature_min=self._value_at(
                        daily.get("temperature_2m_min"),
                        index,
                    ),
                    apparent_temperature_max=self._value_at(
                        daily.get("apparent_temperature_max"),
                        index,
                    ),
                    apparent_temperature_min=self._value_at(
                        daily.get("apparent_temperature_min"),
                        index,
                    ),
                    sunrise=self._value_at(
                        daily.get("sunrise"),
                        index,
                    ),
                    sunset=self._value_at(
                        daily.get("sunset"),
                        index,
                    ),
                    precipitation_sum=self._value_at(
                        daily.get("precipitation_sum"),
                        index,
                    ),
                    rain_sum=self._value_at(
                        daily.get("rain_sum"),
                        index,
                    ),
                    rain_probability_max=self._value_at(
                        daily.get("precipitation_probability_max"),
                        index,
                    ),
                    wind_speed_max=self._value_at(
                        daily.get("wind_speed_10m_max"),
                        index,
                    ),
                )
            )

        response = DailyWeatherResponse(
            latitude=latitude,
            longitude=longitude,
            daily=items,
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=self.DAILY_TTL,
        )

        return response

    async def get_agriculture_context(
        self,
        latitude: float,
        longitude: float,
        reference_time: datetime | None = None,
    ) -> AgricultureContextResponse:
        coordinates = self._coordinate_key(
            latitude,
            longitude,
        )

        cache_key = f"weather:agriculture:{coordinates}"

        cached = await self.redis.get(cache_key)

        if cached:
            return AgricultureContextResponse.model_validate_json(cached)

        if reference_time is None:
            current = await self.get_current(
                latitude,
                longitude,
            )
            reference_time = current.observed_at

        raw = await self.provider.get_agriculture_context(
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

        soil = hourly.get(
            "soil_moisture_0_to_7cm",
            [],
        )

        et0 = hourly.get(
            "et0_fao_evapotranspiration",
            [],
        )

        vpd = hourly.get(
            "vapour_pressure_deficit",
            [],
        )

        nearest_index = self._nearest_time_index(
            times=times,
            reference_time=reference_time,
        )

        response = AgricultureContextResponse(
            latitude=latitude,
            longitude=longitude,
            surface_soil_moisture=(
                self._value_at(
                    soil,
                    nearest_index,
                )
                if nearest_index is not None
                else None
            ),
            evapotranspiration=(
                self._value_at(
                    et0,
                    nearest_index,
                )
                if nearest_index is not None
                else None
            ),
            vapour_pressure_deficit=(
                self._value_at(
                    vpd,
                    nearest_index,
                )
                if nearest_index is not None
                else None
            ),
        )

        await self.redis.set(
            cache_key,
            response.model_dump_json(),
            ex=self.AGRICULTURE_TTL,
        )

        return response
