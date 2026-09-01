import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.dependencies.auth import get_current_user
from app.dependencies.providers import (
    get_alert_provider,
)
from app.integrations.alerts.sachet import (
    SachetAlertProvider,
)
from app.models.user import User
from app.schemas.alert import (
    AlertFeedResponse,
    OfficialAlert,
    RelevantAlertResponse,
    SavedLocationAlertResponse,
)
from app.services.alert_location_service import (
    AlertLocationNotFoundError,
    AlertLocationService,
)
from app.services.alert_service import (
    AlertCacheError,
    AlertService,
)

router = APIRouter(
    prefix="/alerts",
    tags=["Official Alerts"],
)


@router.get(
    "",
    response_model=AlertFeedResponse,
)
async def get_official_alerts(
    provider: Annotated[
        SachetAlertProvider,
        Depends(get_alert_provider),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
):
    service = AlertService(
        provider=provider,
        redis=redis,
    )

    return await service.get_feed()


@router.get(
    "/relevant",
    response_model=RelevantAlertResponse,
)
async def get_relevant_official_alerts(
    latitude: Annotated[
        float,
        Query(ge=-90, le=90),
    ],
    longitude: Annotated[
        float,
        Query(ge=-180, le=180),
    ],
    provider: Annotated[
        SachetAlertProvider,
        Depends(get_alert_provider),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    city: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
):
    service = AlertService(
        provider=provider,
        redis=redis,
    )

    alerts = await service.get_relevant_alerts(
        latitude=latitude,
        longitude=longitude,
        city=city,
    )

    return RelevantAlertResponse(
        latitude=latitude,
        longitude=longitude,
        alerts=alerts,
    )


@router.get(
    "/saved-locations/{location_id}",
    response_model=SavedLocationAlertResponse,
)
async def get_saved_location_alerts(
    location_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    provider: Annotated[
        SachetAlertProvider,
        Depends(get_alert_provider),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
):
    alert_service = AlertService(
        provider=provider,
        redis=redis,
    )

    service = AlertLocationService(
        session=session,
        alert_service=alert_service,
    )

    try:
        return await service.get_for_location(
            user_id=current_user.id,
            location_id=location_id,
        )

    except AlertLocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/primary-location",
    response_model=SavedLocationAlertResponse,
)
async def get_primary_location_alerts(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    provider: Annotated[
        SachetAlertProvider,
        Depends(get_alert_provider),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
):
    alert_service = AlertService(
        provider=provider,
        redis=redis,
    )

    service = AlertLocationService(
        session=session,
        alert_service=alert_service,
    )

    try:
        return await service.get_for_primary_location(user_id=current_user.id)

    except AlertLocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{identifier}",
    response_model=OfficialAlert,
)
async def get_official_alert(
    identifier: str,
    provider: Annotated[
        SachetAlertProvider,
        Depends(get_alert_provider),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
):
    service = AlertService(
        provider=provider,
        redis=redis,
    )

    try:
        return await service.get_alert(identifier=identifier)

    except AlertCacheError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
