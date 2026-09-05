from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.redis import get_redis
from app.dependencies.auth import get_current_user
from app.dependencies.providers import (
    get_email_provider,
    get_google_token_verifier,
)
from app.integrations.email.base import EmailProvider
from app.integrations.google_auth import (
    GoogleTokenVerifier,
)
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService
from app.services.email_verification_service import (
    EmailVerificationService,
)
from app.services.password_reset_service import (
    PasswordResetService,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    # keep your existing response/status definitions
)
async def register(
    payload: RegisterRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    email_provider: Annotated[
        EmailProvider,
        Depends(get_email_provider),
    ],
):
    email_verification_service = build_email_verification_service(
        session=session,
        redis=redis,
        email_provider=email_provider,
    )

    service = AuthService(
        session=session,
        redis=redis,
        email_verification_service=(email_verification_service),
    )

    try:
        user = await service.register(
            name=payload.name,
            email=str(payload.email),
            password=payload.password,
        )
    except ValueError as exc:
        # Preserve whichever status code your
        # current register route already uses.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
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
        message = str(exc)

        if message == ("Email verification required"):
            raise HTTPException(
                status_code=(status.HTTP_403_FORBIDDEN),
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail=message,
        ) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    payload: RefreshRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
):
    service = AuthService(
        session=session,
        redis=redis,
    )

    try:
        (
            access_token,
            refresh_token,
        ) = await service.refresh(payload.refresh_token)

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
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
):
    service = AuthService(
        session=session,
        redis=redis,
    )

    await service.logout(payload.refresh_token)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout_all(
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
):
    service = AuthService(
        session=session,
        redis=redis,
    )

    await service.logout_all(
        user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def build_email_verification_service(
    *,
    session: AsyncSession,
    redis: Redis,
    email_provider: EmailProvider,
) -> EmailVerificationService:
    return EmailVerificationService(
        session=session,
        redis=redis,
        email_provider=email_provider,
        verification_secret=(settings.email_verification_secret),
        code_expire_minutes=(settings.email_verification_code_expire_minutes),
        resend_cooldown_seconds=(settings.email_verification_resend_cooldown_seconds),
        max_attempts=(settings.email_verification_max_attempts),
    )


def build_password_reset_service(
    *,
    session: AsyncSession,
    redis: Redis,
    email_provider: EmailProvider,
) -> PasswordResetService:
    return PasswordResetService(
        session=session,
        redis=redis,
        email_provider=email_provider,
        reset_secret=settings.password_reset_secret,
        code_expire_minutes=(settings.password_reset_code_expire_minutes),
        resend_cooldown_seconds=(settings.password_reset_resend_cooldown_seconds),
        max_attempts=(settings.password_reset_max_attempts),
    )


@router.post(
    "/password/forgot",
    response_model=MessageResponse,
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    email_provider: Annotated[
        EmailProvider,
        Depends(get_email_provider),
    ],
) -> MessageResponse:
    service = build_password_reset_service(
        session=session,
        redis=redis,
        email_provider=email_provider,
    )

    try:
        await service.request_reset(
            email=str(payload.email),
        )
    except ValueError as exc:
        if str(exc) != ("Password reset code recently sent"):
            raise

        # Keep the response generic.
        #
        # Returning 429 only for real accounts
        # could reveal whether an email exists.

    return MessageResponse(
        message=("If an account exists, password reset instructions have been sent.")
    )


@router.post(
    "/password/reset",
    response_model=MessageResponse,
)
async def reset_password(
    payload: ResetPasswordRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    email_provider: Annotated[
        EmailProvider,
        Depends(get_email_provider),
    ],
) -> MessageResponse:
    service = build_password_reset_service(
        session=session,
        redis=redis,
        email_provider=email_provider,
    )

    try:
        await service.reset_password(
            email=str(payload.email),
            code=payload.code,
            new_password=payload.new_password,
        )

    except ValueError as exc:
        message = str(exc)

        if message == ("Too many password reset attempts"):
            raise HTTPException(
                status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    return MessageResponse(message="Password reset successfully")


@router.post(
    "/email-verification/verify",
    response_model=MessageResponse,
)
async def verify_email(
    payload: VerifyEmailRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    email_provider: Annotated[
        EmailProvider,
        Depends(get_email_provider),
    ],
) -> MessageResponse:
    service = build_email_verification_service(
        session=session,
        redis=redis,
        email_provider=email_provider,
    )

    try:
        await service.verify(
            email=str(payload.email),
            code=payload.code,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail=str(exc),
        ) from exc

    return MessageResponse(message="Email verified successfully")


@router.post(
    "/email-verification/resend",
    response_model=MessageResponse,
)
async def resend_email_verification(
    payload: ResendVerificationRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    email_provider: Annotated[
        EmailProvider,
        Depends(get_email_provider),
    ],
) -> MessageResponse:
    service = build_email_verification_service(
        session=session,
        redis=redis,
        email_provider=email_provider,
    )

    try:
        await service.resend(
            email=str(payload.email),
        )

    except ValueError as exc:
        if str(exc) == ("Verification code recently sent"):
            raise HTTPException(
                status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail=str(exc),
        ) from exc

    return MessageResponse(
        message=(
            "If the account requires verification, a verification code has been sent."
        )
    )


@router.post(
    "/google",
    response_model=TokenResponse,
)
async def google_login(
    payload: GoogleLoginRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    google_verifier: Annotated[
        GoogleTokenVerifier,
        Depends(get_google_token_verifier),
    ],
) -> TokenResponse:
    service = AuthService(
        session=session,
        redis=redis,
    )

    try:
        (
            access_token,
            refresh_token,
        ) = await service.google_login(
            id_token=payload.id_token,
            verifier=google_verifier,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail=str(exc),
        ) from exc

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )
