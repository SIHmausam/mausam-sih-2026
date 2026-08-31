import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.location import (
    LocationCreateRequest,
    LocationResponse,
    LocationUpdateRequest,
)
from app.services.location_service import (
    LocationNotFoundError,
    LocationService,
)

router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
)


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_location(
    payload: LocationCreateRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    service = LocationService(session)

    return await service.create_location(
        user_id=current_user.id,
        payload=payload,
    )


@router.get(
    "",
    response_model=list[LocationResponse],
)
async def list_locations(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    service = LocationService(session)

    return await service.list_locations(current_user.id)


@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
)
async def update_location(
    location_id: uuid.UUID,
    payload: LocationUpdateRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    service = LocationService(session)

    try:
        return await service.update_location(
            user_id=current_user.id,
            location_id=location_id,
            payload=payload,
        )

    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location(
    location_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    service = LocationService(session)

    try:
        await service.delete_location(
            user_id=current_user.id,
            location_id=location_id,
        )

    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
