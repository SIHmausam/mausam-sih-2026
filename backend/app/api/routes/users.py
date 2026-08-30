from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.preferences import (
    OnboardingRequest,
    PreferencesPatchRequest,
    PreferencesResponse,
)
from app.schemas.user import UserResponse
from app.services.preference_service import (
    OnboardingAlreadyCompletedError,
    PreferenceService,
    PreferencesNotFoundError,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    return current_user


@router.post(
    "/onboarding",
    response_model=PreferencesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def complete_onboarding(
    payload: OnboardingRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    service = PreferenceService(session)

    try:
        return await service.complete_onboarding(
            current_user.id,
            payload,
        )

    except OnboardingAlreadyCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/preferences",
    response_model=PreferencesResponse,
)
async def get_preferences(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    service = PreferenceService(session)

    try:
        return await service.get_preferences(current_user.id)

    except PreferencesNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/preferences",
    response_model=PreferencesResponse,
)
async def update_preferences(
    payload: PreferencesPatchRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    service = PreferenceService(session)

    try:
        return await service.update_preferences(
            current_user.id,
            payload,
        )

    except PreferencesNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
