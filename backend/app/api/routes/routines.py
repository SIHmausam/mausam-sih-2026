import uuid
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.dependencies.auth import get_current_user
from app.dependencies.providers import (
    get_air_quality_provider,
    get_alert_provider,
    get_weather_provider,
)
from app.integrations.air_quality.base import AirQualityProvider
from app.integrations.alerts.base import AlertProvider
from app.integrations.weather.base import WeatherProvider
from app.models.user import User
from app.schemas.routine import (
    MyDayResponse,
    RoutineCreateRequest,
    RoutineResponse,
    RoutineUpdateRequest,
)
from app.services.air_quality_service import AirQualityService
from app.services.alert_service import AlertService
from app.services.my_day_service import MyDayService
from app.services.routine_service import (
    RoutineLocationNotFoundError,
    RoutineNotFoundError,
    RoutineService,
)
from app.services.weather_context_service import WeatherContextService
from app.services.weather_service import WeatherService

router = APIRouter(
    prefix="/routines",
    tags=["Routines"],
)


@router.post(
    "",
    response_model=RoutineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_routine(
    payload: RoutineCreateRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> RoutineResponse:
    service = RoutineService(
        session=session,
    )

    try:
        routine = await service.create_routine(
            user_id=current_user.id,
            payload=payload,
        )

        return RoutineResponse.model_validate(routine)

    except RoutineLocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[RoutineResponse],
)
async def list_routines(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> list[RoutineResponse]:
    service = RoutineService(
        session=session,
    )

    routines = await service.list_routines(
        user_id=current_user.id,
    )

    return [RoutineResponse.model_validate(routine) for routine in routines]


# IMPORTANT:
# Keep /my-day above /{routine_id}.
#
# Otherwise FastAPI could attempt to interpret
# "my-day" as the routine_id path parameter.
@router.get(
    "/my-day",
    response_model=MyDayResponse,
)
async def get_my_day(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    weather_provider: Annotated[
        WeatherProvider,
        Depends(get_weather_provider),
    ],
    air_quality_provider: Annotated[
        AirQualityProvider,
        Depends(get_air_quality_provider),
    ],
    alert_provider: Annotated[
        AlertProvider,
        Depends(get_alert_provider),
    ],
    target_date: Annotated[
        date | None,
        Query(alias="date"),
    ] = None,
) -> MyDayResponse:
    weather_service = WeatherService(
        provider=weather_provider,
        redis=redis,
    )

    air_quality_service = AirQualityService(
        provider=air_quality_provider,
        redis=redis,
    )

    weather_context_service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
    )

    alert_service = AlertService(
        provider=alert_provider,
        redis=redis,
    )

    my_day_service = MyDayService(
        session=session,
        weather_context_service=weather_context_service,
        alert_service=alert_service,
    )

    return await my_day_service.get_my_day(
        user_id=current_user.id,
        target_date=target_date or datetime.now(UTC).date(),
    )


@router.patch(
    "/{routine_id}",
    response_model=RoutineResponse,
)
async def update_routine(
    routine_id: uuid.UUID,
    payload: RoutineUpdateRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> RoutineResponse:
    service = RoutineService(
        session=session,
    )

    try:
        routine = await service.update_routine(
            user_id=current_user.id,
            routine_id=routine_id,
            payload=payload,
        )

        return RoutineResponse.model_validate(routine)

    except (
        RoutineNotFoundError,
        RoutineLocationNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{routine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_routine(
    routine_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> Response:
    service = RoutineService(
        session=session,
    )

    try:
        await service.delete_routine(
            user_id=current_user.id,
            routine_id=routine_id,
        )

    except RoutineNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
