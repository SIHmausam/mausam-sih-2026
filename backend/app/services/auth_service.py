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
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenService


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        redis: Redis,
    ):
        self.repository = UserRepository(session)
        self.token_service = TokenService(redis)

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
            name=name,
            email=email,
            password_hash=hash_password(password),
        )

        return await self.repository.create(user)

    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[str, str]:
        email = email.lower().strip()

        user = await self.repository.get_by_email(email)

        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("User account is disabled")

        access_token = create_access_token(str(user.id))

        (
            refresh_token,
            jti,
            expires_at,
        ) = create_refresh_token(str(user.id))

        await self.token_service.store_refresh_token(
            jti=jti,
            user_id=str(user.id),
            expires_at=expires_at,
        )

        return access_token, refresh_token

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

        if not user_id or not jti:
            raise ValueError("Invalid refresh token")

        stored_user_id = await self.token_service.get_refresh_token_owner(jti)

        if stored_user_id != user_id:
            raise ValueError("Refresh token has been revoked")

        # Refresh token rotation:
        # invalidate old refresh token
        await self.token_service.revoke_refresh_token(jti)

        access_token = create_access_token(user_id)

        (
            new_refresh_token,
            new_jti,
            expires_at,
        ) = create_refresh_token(user_id)

        await self.token_service.store_refresh_token(
            jti=new_jti,
            user_id=user_id,
            expires_at=expires_at,
        )

        return (
            access_token,
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

        jti = payload.get("jti")

        if jti:
            await self.token_service.revoke_refresh_token(jti)
