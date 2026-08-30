from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(
        get_db_session
    ),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(
        session=session,
        redis=redis,
    )

    try:
        return await service.register(
            name=payload.name,
            email=payload.email,
            password=payload.password,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(
        get_db_session
    ),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(
        session=session,
        redis=redis,
    )

    try:
        (
            access_token,
            refresh_token,
        ) = await service.login(
            email=payload.email,
            password=payload.password,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(
        get_db_session
    ),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(
        session=session,
        redis=redis,
    )

    try:
        (
            access_token,
            refresh_token,
        ) = await service.refresh(
            payload.refresh_token
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    payload: LogoutRequest,
    session: AsyncSession = Depends(
        get_db_session
    ),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(
        session=session,
        redis=redis,
    )

    await service.logout(
        payload.refresh_token
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )