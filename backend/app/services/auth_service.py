import logging
import uuid
from datetime import UTC, datetime

import jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.auth_session import AuthSession
from app.models.user import User
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository
from app.services.email_verification_service import (
    EmailVerificationService,
)
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        redis: Redis,
        email_verification_service: (EmailVerificationService | None) = None,
    ):
        self.session = session
        self.repository = UserRepository(session)
        self.auth_session_repository = AuthSessionRepository(session)
        self.token_service = TokenService(redis)
        self.email_verification_service = email_verification_service

    async def register(
        self,
        name: str,
        email: str,
        password: str,
    ) -> User:
        email = email.lower().strip()

        existing_user = await self.repository.get_by_email(email)

        if existing_user:
            raise ValueError("Email already registered")

        user = User(
            name=name.strip(),
            email=email,
            password_hash=hash_password(password),
            email_verified_at=None,
        )

        user = await self.repository.create(user)

        await self.session.commit()

        if self.email_verification_service is not None:
            try:
                await self.email_verification_service.send_verification_code(user=user)
            except Exception:
                logger.exception(
                    "Failed to send verification email for user_id=%s",
                    user.id,
                )

        return user

    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[str, str]:
        email = email.lower().strip()

        user = await self.repository.get_by_email(email)

        if user is None:
            raise ValueError("Invalid credentials")

        if user.password_hash is None or not verify_password(
            password,
            user.password_hash,
        ):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("User account is disabled")

        if user.email_verified_at is None:
            raise ValueError("Email verification required")

        session_id = uuid.uuid4()
        family_id = uuid.uuid4()

        access_token = create_access_token(
            str(user.id),
            session_id=str(session_id),
            auth_version=user.auth_version,
        )

        (
            refresh_token,
            refresh_jti,
            refresh_expires_at,
        ) = create_refresh_token(
            str(user.id),
            session_id=str(session_id),
            family_id=str(family_id),
            auth_version=user.auth_version,
        )

        auth_session = AuthSession(
            id=session_id,
            user_id=user.id,
            family_id=family_id,
            expires_at=refresh_expires_at,
        )

        await self.auth_session_repository.create(auth_session)

        await self.token_service.store_session_refresh_token(
            jti=refresh_jti,
            user_id=str(user.id),
            session_id=str(session_id),
            family_id=str(family_id),
            expires_at=refresh_expires_at,
        )

        await self.session.commit()

        return (
            access_token,
            refresh_token,
        )

    async def refresh(
        self,
        refresh_token: str,
    ) -> tuple[str, str]:
        try:
            payload = decode_token(refresh_token)
        except jwt.InvalidTokenError as exc:
            raise ValueError("Invalid or expired refresh token") from exc

        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id = payload.get("sub")
        jti = payload.get("jti")
        session_id = payload.get("sid")
        family_id = payload.get("family")
        auth_version = payload.get("av")

        if (
            not user_id
            or not jti
            or not session_id
            or not family_id
            or auth_version is None
        ):
            raise ValueError("Invalid refresh token")

        try:
            user_uuid = uuid.UUID(str(user_id))
            session_uuid = uuid.UUID(str(session_id))
            family_uuid = uuid.UUID(str(family_id))
        except ValueError as exc:
            raise ValueError("Invalid refresh token") from exc

        user_id = str(user_uuid)
        session_id = str(session_uuid)
        family_id = str(family_uuid)

        user = await self.repository.get_by_id(user_uuid)

        if user is None:
            raise ValueError("Invalid refresh token")

        if not user.is_active:
            raise ValueError("User account is disabled")

        if user.auth_version != auth_version:
            raise ValueError("Refresh token has been revoked")

        auth_session = await self.auth_session_repository.get_by_id(
            session_id=session_uuid
        )

        if auth_session is None:
            raise ValueError("Refresh session not found")

        if auth_session.user_id != user.id:
            raise ValueError("Invalid refresh session")

        if auth_session.family_id != family_uuid:
            raise ValueError("Invalid refresh family")

        now = datetime.now(UTC)

        if auth_session.revoked_at is not None:
            raise ValueError("Refresh session has been revoked")

        if auth_session.expires_at <= now:
            raise ValueError("Refresh session has expired")

        family_revoked = await self.token_service.is_refresh_family_revoked(
            family_id=family_id
        )

        if family_revoked:
            raise ValueError("Refresh family has been revoked")

        active_token = await self.token_service.get_active_refresh_token(jti=jti)

        if active_token is not None and (
            active_token.get("user_id") != user_id
            or active_token.get("session_id") != session_id
            or active_token.get("family_id") != family_id
        ):
            raise ValueError("Invalid refresh token")

        consume_result = await self.token_service.consume_refresh_token(
            jti=jti,
            family_id=family_id,
            expires_at=auth_session.expires_at,
        )

        if consume_result == "reused":
            await self.token_service.revoke_refresh_family(
                family_id=family_id,
                expires_at=auth_session.expires_at,
            )

            await self.auth_session_repository.revoke(auth_session=auth_session)

            await self.session.commit()

            raise ValueError("Refresh token reuse detected")

        # Token was never active or its active state has already
        # disappeared.
        if consume_result == "missing":
            raise ValueError("Refresh token has been revoked")

        if consume_result != "consumed":
            raise ValueError("Invalid refresh token")

        await self.auth_session_repository.touch(auth_session=auth_session)

        new_access_token = create_access_token(
            user_id,
            session_id=session_id,
            auth_version=user.auth_version,
        )

        (
            new_refresh_token,
            new_refresh_jti,
            new_refresh_expires_at,
        ) = create_refresh_token(
            user_id,
            session_id=session_id,
            family_id=family_id,
            auth_version=user.auth_version,
        )

        auth_session.expires_at = new_refresh_expires_at

        await self.token_service.store_session_refresh_token(
            jti=new_refresh_jti,
            user_id=user_id,
            session_id=session_id,
            family_id=family_id,
            expires_at=new_refresh_expires_at,
        )

        await self.session.commit()

        return (
            new_access_token,
            new_refresh_token,
        )

    async def logout(
        self,
        refresh_token: str,
    ) -> None:
        try:
            payload = decode_token(refresh_token)
        except jwt.InvalidTokenError:
            return

        if payload.get("type") != "refresh":
            return

        user_id = payload.get("sub")
        jti = payload.get("jti")
        session_id = payload.get("sid")
        family_id = payload.get("family")

        if not user_id or not session_id or not family_id:
            return

        try:
            user_uuid = uuid.UUID(str(user_id))
            session_uuid = uuid.UUID(str(session_id))
            family_uuid = uuid.UUID(str(family_id))
        except ValueError:
            return

        auth_session = await self.auth_session_repository.get_by_id(
            session_id=session_uuid
        )

        if auth_session is None:
            return

        if auth_session.user_id != user_uuid:
            return

        if auth_session.family_id != family_uuid:
            return

        await self.token_service.revoke_refresh_family(
            family_id=str(family_uuid),
            expires_at=auth_session.expires_at,
        )

        if jti:
            await self.token_service.remove_active_refresh_token(jti=jti)

        await self.auth_session_repository.revoke(auth_session=auth_session)

        await self.session.commit()

    async def logout_all(
        self,
        *,
        user: User,
    ) -> None:
        active_sessions = await self.auth_session_repository.list_active_for_user(
            user_id=user.id
        )

        # Mark every active refresh family as revoked in Redis.
        for auth_session in active_sessions:
            await self.token_service.revoke_refresh_family(
                family_id=str(auth_session.family_id),
                expires_at=auth_session.expires_at,
            )

        # Revoke every DB session belonging to the user.
        await self.auth_session_repository.revoke_all_for_user(user_id=user.id)

        # Incrementing auth_version invalidates every old
        # access/refresh token containing the previous "av".
        await self.repository.increment_auth_version(user=user)

        await self.session.commit()
