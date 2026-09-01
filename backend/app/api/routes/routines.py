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
from app.schemas.routine import (
    RoutineCreateRequest,
    RoutineResponse,
    RoutineUpdateRequest,
)
from app.services.routine_service import (
    RoutineLocationNotFoundError,
    RoutineNotFoundError,
    RoutineService,
)

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
):
    service = RoutineService(session)

    try:
        return await service.create_routine(
            user_id=current_user.id,
            payload=payload,
        )

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
):
    service = RoutineService(session)

    return await service.list_routines(user_id=current_user.id)


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
):
    service = RoutineService(session)

    try:
        return await service.update_routine(
            user_id=current_user.id,
            routine_id=routine_id,
            payload=payload,
        )

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
):
    service = RoutineService(session)

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

    return Response(status_code=status.HTTP_204_NO_CONTENT)
