from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.dependencies.providers import (
    get_air_quality_provider,
    get_weather_provider,
)
from app.integrations.air_quality.open_meteo import (
    OpenMeteoAirQualityProvider,
)
from app.integrations.weather.open_meteo import (
    OpenMeteoWeatherProvider,
)
from app.schemas.weather import (
    AgricultureContextResponse,
    CurrentWeatherResponse,
    DailyWeatherResponse,
    HourlyWeatherResponse,
    WeatherContextResponse,
)
from app.services.air_quality_service import (
    AirQualityService,
)
from app.services.weather_context_service import (
    WeatherContextService,
)
from app.services.weather_service import WeatherService

router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


@router.get(
    "/current",
    response_model=CurrentWeatherResponse,
)
async def get_current_weather(
    latitude: Annotated[
        float,
        Query(ge=-90, le=90),
    ],
    longitude: Annotated[
        float,
        Query(ge=-180, le=180),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    provider: Annotated[
        OpenMeteoWeatherProvider,
        Depends(get_weather_provider),
    ],
):
    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    return await service.get_current(
        latitude,
        longitude,
    )


@router.get(
    "/agriculture",
    response_model=AgricultureContextResponse,
)
async def get_agriculture_context(
    latitude: Annotated[
        float,
        Query(ge=-90, le=90),
    ],
    longitude: Annotated[
        float,
        Query(ge=-180, le=180),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    provider: Annotated[
        OpenMeteoWeatherProvider,
        Depends(get_weather_provider),
    ],
):
    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    return await service.get_agriculture_context(
        latitude,
        longitude,
    )


@router.get(
    "/hourly",
    response_model=HourlyWeatherResponse,
)
async def get_hourly_weather(
    latitude: Annotated[
        float,
        Query(ge=-90, le=90),
    ],
    longitude: Annotated[
        float,
        Query(ge=-180, le=180),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    provider: Annotated[
        OpenMeteoWeatherProvider,
        Depends(get_weather_provider),
    ],
):
    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    return await service.get_hourly(
        latitude,
        longitude,
    )


@router.get(
    "/daily",
    response_model=DailyWeatherResponse,
)
async def get_daily_weather(
    latitude: Annotated[
        float,
        Query(ge=-90, le=90),
    ],
    longitude: Annotated[
        float,
        Query(ge=-180, le=180),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    provider: Annotated[
        OpenMeteoWeatherProvider,
        Depends(get_weather_provider),
    ],
):
    service = WeatherService(
        provider=provider,
        redis=redis,
    )

    return await service.get_daily(
        latitude,
        longitude,
    )


@router.get(
    "/context",
    response_model=WeatherContextResponse,
)
async def get_weather_context(
    latitude: Annotated[
        float,
        Query(ge=-90, le=90),
    ],
    longitude: Annotated[
        float,
        Query(ge=-180, le=180),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    weather_provider: Annotated[
        OpenMeteoWeatherProvider,
        Depends(get_weather_provider),
    ],
    air_quality_provider: Annotated[
        OpenMeteoAirQualityProvider,
        Depends(get_air_quality_provider),
    ],
):
    weather_service = WeatherService(
        provider=weather_provider,
        redis=redis,
    )

    air_quality_service = AirQualityService(
        provider=air_quality_provider,
        redis=redis,
    )

    context_service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    return await context_service.get_context(
        latitude,
        longitude,
    )
