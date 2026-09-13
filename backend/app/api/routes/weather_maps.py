from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from app.dependencies.auth import (
    get_current_user,
)
from app.dependencies.providers import (
    get_weather_map_service,
)
from app.integrations.weather_maps.base import (
    WeatherMapProviderError,
)
from app.models.user import User
from app.schemas.weather_map import (
    WeatherMapConfigResponse,
    WeatherMapLayer,
)
from app.services.weather_map_service import (
    WeatherMapRateLimitError,
    WeatherMapService,
    WeatherMapTileValidationError,
)

router = APIRouter(
    prefix="/weather/maps",
    tags=["Weather Maps"],
)


@router.get(
    "/config",
    response_model=WeatherMapConfigResponse,
)
async def get_weather_map_config(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    service: Annotated[
        WeatherMapService,
        Depends(get_weather_map_service),
    ],
):
    del current_user

    return service.get_config()


@router.get(
    "/tiles/{layer}/{z}/{x}/{y}",
    response_class=Response,
)
async def get_weather_map_tile(
    layer: WeatherMapLayer,
    z: int,
    x: int,
    y: int,

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    service: Annotated[
        WeatherMapService,
        Depends(get_weather_map_service),
    ],
):
    try:
        tile = await service.get_tile(
            user_id=current_user.id,
            layer=layer,
            zoom=z,
            x=x,
            y=y,
        )

    except WeatherMapTileValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(exc),
        ) from exc

    except WeatherMapRateLimitError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
            ),
            detail=str(exc),
        ) from exc

    except WeatherMapProviderError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Weather map provider "
                "is unavailable"
            ),
        ) from exc

    return Response(
        content=tile.content,
        media_type="image/png",
        headers={
            "Cache-Control": (
                "private, max-age="
                f"{service.cache_ttl_seconds}"
            ),
            "X-Weather-Map-Cache": (
                "HIT"
                if tile.cache_hit
                else "MISS"
            ),
        },
    )