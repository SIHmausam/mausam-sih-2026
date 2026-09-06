from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.services.weather_context_service import (
    WeatherContextService,
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