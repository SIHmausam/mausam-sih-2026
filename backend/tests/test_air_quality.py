import pytest
from httpx import AsyncClient

from app.core.redis import get_redis
from app.dependencies.providers import (
    get_air_quality_provider,
)
from app.main import app
from app.schemas.air_quality import (
    CurrentAirQualityResponse,
)
from app.services.air_quality_service import (
    AirQualityService,
)


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


class FakeAirQualityProvider:
    def __init__(self):
        self.current_calls = 0
        self.hourly_calls = 0

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
                "us_aqi": 82.0,
                "european_aqi": 47.0,
                "pm2_5": 22.1,
                "pm10": 39.4,
                "nitrogen_dioxide": 12.3,
                "sulphur_dioxide": 5.4,
                "carbon_monoxide": 180.2,
                "ozone": 75.6,
                "uv_index": 5.1,
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
                "us_aqi": [
                    82.0,
                    85.0,
                ],
                "european_aqi": [
                    47.0,
                    49.0,
                ],
                "pm2_5": [
                    22.1,
                    23.0,
                ],
                "pm10": [
                    39.4,
                    41.0,
                ],
                "nitrogen_dioxide": [
                    12.3,
                    13.1,
                ],
                "sulphur_dioxide": [
                    5.4,
                    5.7,
                ],
                "carbon_monoxide": [
                    180.2,
                    185.0,
                ],
                "ozone": [
                    75.6,
                    77.0,
                ],
                "uv_index": [
                    5.1,
                    5.5,
                ],
            },
        }


class EuropeanOnlyAirQualityProvider(FakeAirQualityProvider):
    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ):
        self.current_calls += 1

        return {
            "current": {
                "us_aqi": None,
                "european_aqi": 52.0,
                "pm2_5": 20.0,
                "pm10": 35.0,
                "nitrogen_dioxide": 10.0,
                "sulphur_dioxide": 4.0,
                "carbon_monoxide": 170.0,
                "ozone": 70.0,
                "uv_index": 4.0,
            }
        }


class NoAqiAirQualityProvider(FakeAirQualityProvider):
    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ):
        self.current_calls += 1

        return {
            "current": {
                "us_aqi": None,
                "european_aqi": None,
                "pm2_5": 20.0,
                "pm10": 35.0,
                "nitrogen_dioxide": 10.0,
                "sulphur_dioxide": 4.0,
                "carbon_monoxide": 170.0,
                "ozone": 70.0,
                "uv_index": 4.0,
            }
        }


class FailingAirQualityProvider(FakeAirQualityProvider):
    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ):
        raise RuntimeError("Air quality provider unavailable")


@pytest.mark.asyncio
async def test_current_air_quality_is_normalized():
    provider = FakeAirQualityProvider()
    redis = FakeRedis()

    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.aqi == 82.0
    assert response.aqi_standard == "us"

    assert response.us_aqi == 82.0
    assert response.european_aqi == 47.0

    assert response.pm2_5 == 22.1
    assert response.pm10 == 39.4

    assert response.nitrogen_dioxide == 12.3
    assert response.sulphur_dioxide == 5.4
    assert response.carbon_monoxide == 180.2
    assert response.ozone == 75.6

    assert response.uv_index == 5.1

    assert provider.current_calls == 1


@pytest.mark.asyncio
async def test_us_aqi_is_used_as_normalized_aqi():
    provider = FakeAirQualityProvider()
    redis = FakeRedis()

    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.aqi == response.us_aqi
    assert response.aqi_standard == "us"


@pytest.mark.asyncio
async def test_european_aqi_is_used_when_us_aqi_missing():
    provider = EuropeanOnlyAirQualityProvider()
    redis = FakeRedis()

    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.us_aqi is None
    assert response.european_aqi == 52.0

    assert response.aqi == 52.0
    assert response.aqi_standard == "european"


@pytest.mark.asyncio
async def test_normalized_aqi_is_none_when_no_aqi_available():
    provider = NoAqiAirQualityProvider()
    redis = FakeRedis()

    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.us_aqi is None
    assert response.european_aqi is None

    assert response.aqi is None
    assert response.aqi_standard is None


@pytest.mark.asyncio
async def test_hourly_air_quality_is_normalized():
    provider = FakeAirQualityProvider()
    redis = FakeRedis()

    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_hourly(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert len(response.hourly) == 2

    first = response.hourly[0]

    assert first.us_aqi == 82.0
    assert first.european_aqi == 47.0

    assert first.pm2_5 == 22.1
    assert first.pm10 == 39.4

    assert first.nitrogen_dioxide == 12.3
    assert first.sulphur_dioxide == 5.4
    assert first.carbon_monoxide == 180.2
    assert first.ozone == 75.6

    assert first.uv_index == 5.1

    second = response.hourly[1]

    assert second.us_aqi == 85.0
    assert second.pm2_5 == 23.0
    assert second.uv_index == 5.5

    assert provider.hourly_calls == 1


@pytest.mark.asyncio
async def test_current_air_quality_uses_cache():
    provider = FakeAirQualityProvider()
    redis = FakeRedis()

    service = AirQualityService(
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
async def test_cached_current_air_quality_skips_provider():
    provider = FakeAirQualityProvider()
    redis = FakeRedis()

    cached_response = CurrentAirQualityResponse(
        latitude=28.6139,
        longitude=77.2090,
        aqi=65.0,
        aqi_standard="us",
        us_aqi=65.0,
        european_aqi=40.0,
        pm2_5=18.0,
        pm10=30.0,
        nitrogen_dioxide=9.0,
        sulphur_dioxide=3.0,
        carbon_monoxide=150.0,
        ozone=60.0,
        uv_index=4.0,
    )

    cache_key = "air_quality:current:28.614:77.209"

    redis.storage[cache_key] = cached_response.model_dump_json()

    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    response = await service.get_current(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert response.aqi == 65.0
    assert response.pm2_5 == 18.0

    assert provider.current_calls == 0


@pytest.mark.asyncio
async def test_hourly_air_quality_uses_cache():
    provider = FakeAirQualityProvider()
    redis = FakeRedis()

    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    first_response = await service.get_hourly(
        latitude=28.6139,
        longitude=77.2090,
    )

    second_response = await service.get_hourly(
        latitude=28.6139,
        longitude=77.2090,
    )

    assert first_response == second_response

    assert provider.hourly_calls == 1


@pytest.mark.asyncio
async def test_provider_failure_is_propagated():
    provider = FailingAirQualityProvider()
    redis = FakeRedis()

    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    with pytest.raises(
        RuntimeError,
        match="Air quality provider unavailable",
    ):
        await service.get_current(
            latitude=28.6139,
            longitude=77.2090,
        )


@pytest.mark.asyncio
async def test_invalid_latitude_returns_422(
    client: AsyncClient,
):
    provider = FakeAirQualityProvider()
    redis = FakeRedis()

    async def override_redis():
        return redis

    def override_provider():
        return provider

    app.dependency_overrides[get_redis] = override_redis

    app.dependency_overrides[get_air_quality_provider] = override_provider

    try:
        response = await client.get(
            "/api/v1/air-quality/current",
            params={
                "latitude": 91,
                "longitude": 77.2090,
            },
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(
            get_air_quality_provider,
            None,
        )
        app.dependency_overrides.pop(
            get_redis,
            None,
        )


@pytest.mark.asyncio
async def test_invalid_longitude_returns_422(
    client: AsyncClient,
):
    provider = FakeAirQualityProvider()
    redis = FakeRedis()

    async def override_redis():
        return redis

    def override_provider():
        return provider

    app.dependency_overrides[get_redis] = override_redis

    app.dependency_overrides[get_air_quality_provider] = override_provider

    try:
        response = await client.get(
            "/api/v1/air-quality/current",
            params={
                "latitude": 28.6139,
                "longitude": 181,
            },
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(
            get_air_quality_provider,
            None,
        )
        app.dependency_overrides.pop(
            get_redis,
            None,
        )
