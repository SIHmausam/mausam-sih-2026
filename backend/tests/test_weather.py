import pytest
from httpx import AsyncClient

from app.core.redis import get_redis
from app.dependencies.providers import (
    get_weather_provider,
)
from app.main import app
from app.schemas.weather import CurrentWeatherResponse
from app.services.weather_service import WeatherService


class FakeRedis:
    def __init__(self):
        self.storage: dict[str, str] = {}

    async def get(
        self,
        key: str,
    ) -> str | None:
        return self.storage.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
    ):
        self.storage[key] = value


class FakeWeatherProvider:
    def __init__(self):
        self.current_calls = 0
        self.hourly_calls = 0
        self.daily_calls = 0
        self.agriculture_calls = 0

    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ):
        self.current_calls += 1

        return {
            "latitude": latitude,
            "longitude": longitude,
            "current": {
                "temperature_2m": 30.5,
                "relative_humidity_2m": 68,
                "apparent_temperature": 34.2,
                "precipitation": 1.2,
                "rain": 1.0,
                "weather_code": 61,
                "wind_speed_10m": 12.4,
                "is_day": 1,
            },
        }

    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
    ):
        self.hourly_calls += 1

        return {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": {
                "time": [
                    "2026-08-31T10:00",
                    "2026-08-31T11:00",
                ],
                "temperature_2m": [
                    29.5,
                    30.5,
                ],
                "relative_humidity_2m": [
                    70,
                    68,
                ],
                "apparent_temperature": [
                    33.0,
                    34.2,
                ],
                "precipitation": [
                    0.5,
                    1.2,
                ],
                "rain": [
                    0.4,
                    1.0,
                ],
                "precipitation_probability": [
                    40,
                    70,
                ],
                "weather_code": [
                    3,
                    61,
                ],
                "wind_speed_10m": [
                    10.0,
                    12.4,
                ],
                "visibility": [
                    15000,
                    12000,
                ],
            },
        }

    async def get_daily(
        self,
        latitude: float,
        longitude: float,
    ):
        self.daily_calls += 1

        return {
            "latitude": latitude,
            "longitude": longitude,
            "daily": {
                "time": [
                    "2026-08-31",
                    "2026-09-01",
                ],
                "weather_code": [
                    61,
                    3,
                ],
                "temperature_2m_max": [
                    34.0,
                    35.0,
                ],
                "temperature_2m_min": [
                    26.0,
                    27.0,
                ],
                "apparent_temperature_max": [
                    39.0,
                    40.0,
                ],
                "apparent_temperature_min": [
                    28.0,
                    29.0,
                ],
                "sunrise": [
                    "2026-08-31T05:58",
                    "2026-09-01T05:59",
                ],
                "sunset": [
                    "2026-08-31T18:40",
                    "2026-09-01T18:39",
                ],
                "precipitation_sum": [
                    5.2,
                    1.0,
                ],
                "rain_sum": [
                    5.0,
                    0.8,
                ],
                "precipitation_probability_max": [
                    80,
                    30,
                ],
                "wind_speed_10m_max": [
                    18.0,
                    14.0,
                ],
            },
        }

    async def get_agriculture_context(
        self,
        latitude: float,
        longitude: float,
    ):
        self.agriculture_calls += 1

        return {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": {
                "time": [
                    "2026-08-31T10:00",
                ],
                "soil_moisture_0_to_7cm": [
                    0.32,
                ],
                "et0_fao_evapotranspiration": [
                    0.18,
                ],
                "vapour_pressure_deficit": [
                    0.9,
                ],
            },
        }


class FailingWeatherProvider(FakeWeatherProvider):
    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ):
        raise RuntimeError("Weather provider unavailable")


@pytest.mark.asyncio
async def test_current_weather_is_normalized():
    provider = FakeWeatherProvider()
    redis = FakeRedis()

    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.temperature == 30.5
    assert response.humidity == 68
    assert response.apparent_temperature == 34.2
    assert response.precipitation == 1.2
    assert response.rain == 1.0
    assert response.weather_code == 61
    assert response.wind_speed == 12.4
    assert response.is_daylight is True

    assert provider.current_calls == 1


@pytest.mark.asyncio
async def test_hourly_weather_is_normalized():
    provider = FakeWeatherProvider()
    redis = FakeRedis()

    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_hourly(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert len(response.hourly) == 2

    first = response.hourly[0]

    assert first.temperature == 29.5
    assert first.humidity == 70
    assert first.apparent_temperature == 33.0
    assert first.precipitation == 0.5
    assert first.rain == 0.4
    assert first.rain_probability == 40
    assert first.weather_code == 3
    assert first.wind_speed == 10.0
    assert first.visibility == 15000

    assert provider.hourly_calls == 1


@pytest.mark.asyncio
async def test_daily_weather_is_normalized():
    provider = FakeWeatherProvider()
    redis = FakeRedis()

    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_daily(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert len(response.daily) == 2

    first = response.daily[0]

    assert first.date == "2026-08-31"
    assert first.weather_code == 61
    assert first.temperature_max == 34.0
    assert first.temperature_min == 26.0
    assert first.apparent_temperature_max == 39.0
    assert first.apparent_temperature_min == 28.0
    assert first.precipitation_sum == 5.2
    assert first.rain_sum == 5.0
    assert first.rain_probability_max == 80
    assert first.wind_speed_max == 18.0

    assert provider.daily_calls == 1


@pytest.mark.asyncio
async def test_agriculture_context_is_normalized():
    provider = FakeWeatherProvider()
    redis = FakeRedis()

    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_agriculture_context(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.surface_soil_moisture == 0.32
    assert response.evapotranspiration == 0.18
    assert response.vapour_pressure_deficit == 0.9

    assert provider.agriculture_calls == 1


@pytest.mark.asyncio
async def test_current_weather_uses_cache():
    provider = FakeWeatherProvider()
    redis = FakeRedis()

    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    first_response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    second_response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert first_response == second_response

    assert provider.current_calls == 1


@pytest.mark.asyncio
async def test_cached_current_weather_skips_provider():
    provider = FakeWeatherProvider()
    redis = FakeRedis()

    cached_response = CurrentWeatherResponse(
        latitude=28.6139,
        longitude=77.2090,
        temperature=25.0,
        apparent_temperature=26.0,
        humidity=60,
        precipitation=0,
        rain=0,
        weather_code=1,
        wind_speed=5.0,
        is_daylight=True,
    )

    cache_key = "weather:current:28.614:77.209"

    redis.storage[cache_key] = cached_response.model_dump_json()

    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.temperature == 25.0

    assert provider.current_calls == 0


@pytest.mark.asyncio
async def test_provider_failure_is_propagated():
    provider = FailingWeatherProvider()
    redis = FakeRedis()

    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    with pytest.raises(
        RuntimeError,
        match="Weather provider unavailable",
    ):
        await service.get_current(
            latitude=28.6139,
            longitude=77.2090,
        )


@pytest.mark.asyncio
async def test_invalid_latitude_returns_422(
    client: AsyncClient,
):
    provider = FakeWeatherProvider()
    redis = FakeRedis()

    async def override_redis():
        return redis

    def override_provider():
        return provider

    app.dependency_overrides[get_redis] = override_redis

    app.dependency_overrides[get_weather_provider] = override_provider

    response = await client.get(
        "/api/v1/weather/current",
        params={
            "latitude": 91,
            "longitude": 77.2090,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_longitude_returns_422(
    client: AsyncClient,
):
    provider = FakeWeatherProvider()
    redis = FakeRedis()

    async def override_redis():
        return redis

    def override_provider():
        return provider

    app.dependency_overrides[get_redis] = override_redis

    app.dependency_overrides[get_weather_provider] = override_provider

    response = await client.get(
        "/api/v1/weather/current",
        params={
            "latitude": 28.6139,
            "longitude": 181,
        },
    )

    assert response.status_code == 422
