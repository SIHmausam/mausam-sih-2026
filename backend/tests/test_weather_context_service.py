from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.schemas.weather import (
    CurrentWeatherResponse,
)
from app.services.weather_context_service import (
    WeatherContextService,
)


def build_successful_services():
    latitude = 28.646748
    longitude = 77.48004

    weather_service = SimpleNamespace(
        get_current=AsyncMock(
            return_value=CurrentWeatherResponse(
                latitude=latitude,
                longitude=longitude,
                temperature=31.0,
            )
        ),
        get_hourly=AsyncMock(
            return_value=SimpleNamespace(
                hourly=[],
            )
        ),
        get_daily=AsyncMock(
            return_value=SimpleNamespace(
                daily=[],
            )
        ),
        get_agriculture_context=AsyncMock(
            return_value=None,
        ),
    )

    air_quality_service = SimpleNamespace(
        get_current=AsyncMock(
            return_value=None,
        ),
        get_hourly=AsyncMock(
            return_value=SimpleNamespace(
                hourly=[],
            )
        ),
    )

    return (
        weather_service,
        air_quality_service,
    )


def build_connect_error():
    request = httpx.Request(
        "GET",
        "https://example.com",
    )

    return httpx.ConnectError(
        "Provider unavailable",
        request=request,
    )

@pytest.mark.asyncio
async def test_weather_context_returns_unavailable_on_429():
    request = httpx.Request(
        "GET",
        "https://api.open-meteo.com/v1/forecast",
    )

    response = httpx.Response(
        429,
        request=request,
    )

    error = httpx.HTTPStatusError(
        "Too Many Requests",
        request=request,
        response=response,
    )

    weather_service = SimpleNamespace(
        get_current=AsyncMock(
            side_effect=error,
        ),
        get_hourly=AsyncMock(),
        get_daily=AsyncMock(),
        get_agriculture_context=AsyncMock(),
    )

    air_quality_service = SimpleNamespace(
        get_current=AsyncMock(),
        get_hourly=AsyncMock(),
    )

    service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    result = await service.get_context(
        latitude=28.646748,
        longitude=77.48004,
    )

    assert result.available is False

    assert result.message == (
        "Weather data is temporarily unavailable. "
        "Please try again shortly."
    )

    assert result.latitude == 28.646748
    assert result.longitude == 77.48004

    assert result.current.latitude == 28.646748
    assert result.current.longitude == 77.48004

    assert result.current.temperature is None

    assert result.hourly == []
    assert result.daily == []

    assert result.agriculture is None
    assert result.air_quality is None

@pytest.mark.asyncio
async def test_current_air_quality_failure_is_non_fatal():
    (
        weather_service,
        air_quality_service,
    ) = build_successful_services()

    air_quality_service.get_current.side_effect = (
        build_connect_error()
    )

    service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    result = await service.get_context(
        latitude=28.646748,
        longitude=77.48004,
    )

    assert result.available is True
    assert result.current.temperature == 31.0
    assert result.air_quality is None

    air_quality_service.get_current.assert_awaited_once()


@pytest.mark.asyncio
async def test_hourly_air_quality_failure_is_non_fatal():
    (
        weather_service,
        air_quality_service,
    ) = build_successful_services()

    air_quality_service.get_hourly.side_effect = (
        build_connect_error()
    )

    service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    result = await service.get_context(
        latitude=28.646748,
        longitude=77.48004,
    )

    assert result.available is True
    assert result.current.temperature == 31.0
    assert result.hourly_air_quality == []

    air_quality_service.get_hourly.assert_awaited_once()


@pytest.mark.asyncio
async def test_agriculture_failure_is_non_fatal():
    (
        weather_service,
        air_quality_service,
    ) = build_successful_services()

    weather_service.get_agriculture_context.side_effect = (
        build_connect_error()
    )

    service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    result = await service.get_context(
        latitude=28.646748,
        longitude=77.48004,
    )

    assert result.available is True
    assert result.current.temperature == 31.0
    assert result.agriculture is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name",
    [
        "get_current",
        "get_hourly",
        "get_daily",
    ],
)
async def test_core_weather_failure_returns_unavailable(
    method_name,
):
    (
        weather_service,
        air_quality_service,
    ) = build_successful_services()

    getattr(
        weather_service,
        method_name,
    ).side_effect = build_connect_error()

    service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    result = await service.get_context(
        latitude=28.646748,
        longitude=77.48004,
    )

    assert result.available is False

    assert result.message == (
        "Weather data is temporarily unavailable. "
        "Please try again shortly."
    )

    assert result.current.temperature is None
    assert result.hourly == []
    assert result.daily == []


@pytest.mark.asyncio
async def test_unexpected_exception_is_not_swallowed():
    (
        weather_service,
        air_quality_service,
    ) = build_successful_services()

    weather_service.get_current.side_effect = RuntimeError(
        "Unexpected programming error"
    )

    service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected programming error",
    ):
        await service.get_context(
            latitude=28.646748,
            longitude=77.48004,
        )
