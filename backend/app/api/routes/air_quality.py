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
)
from app.integrations.air_quality.open_meteo import (
    OpenMeteoAirQualityProvider,
)
from app.schemas.air_quality import (
    CurrentAirQualityResponse,
    HourlyAirQualityResponse,
)
from app.services.air_quality_service import (
    AirQualityService,
)

router = APIRouter(
    prefix="/air-quality",
    tags=["Air Quality"],
)


@router.get(
    "/current",
    response_model=CurrentAirQualityResponse,
)
async def get_current_air_quality(
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
        OpenMeteoAirQualityProvider,
        Depends(get_air_quality_provider),
    ],
):
    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    return await service.get_current(
        latitude,
        longitude,
    )


@router.get(
    "/hourly",
    response_model=HourlyAirQualityResponse,
)
async def get_hourly_air_quality(
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
        OpenMeteoAirQualityProvider,
        Depends(get_air_quality_provider),
    ],
):
    service = AirQualityService(
        provider=provider,
        redis=redis,
    )

    return await service.get_hourly(
        latitude,
        longitude,
    )
