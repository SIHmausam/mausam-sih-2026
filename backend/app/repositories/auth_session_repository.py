import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_session import AuthSession


class AuthSessionRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        auth_session: AuthSession,
    ) -> AuthSession:
        self.session.add(auth_session)

        await self.session.flush()

        return auth_session

    async def get_by_id(
        self,
        *,
        session_id: uuid.UUID,
    ) -> AuthSession | None:
        result = await self.session.execute(
            select(AuthSession).where(AuthSession.id == session_id)
        )

        return result.scalar_one_or_none()

    async def get_by_family_id(
        self,
        *,
        family_id: uuid.UUID,
    ) -> AuthSession | None:
        result = await self.session.execute(
            select(AuthSession).where(AuthSession.family_id == family_id)
        )

        return result.scalar_one_or_none()

    async def get_active_by_id(
        self,
        *,
        session_id: uuid.UUID,
    ) -> AuthSession | None:
        now = datetime.now(UTC)

        result = await self.session.execute(
            select(AuthSession).where(
                AuthSession.id == session_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
        )

        return result.scalar_one_or_none()

    async def list_active_for_user(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[AuthSession]:
        now = datetime.now(UTC)

        result = await self.session.execute(
            select(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
            .order_by(AuthSession.last_used_at.desc())
        )

        return list(result.scalars().all())

    async def touch(
        self,
        *,
        auth_session: AuthSession,
    ) -> None:
        auth_session.last_used_at = datetime.now(UTC)

        await self.session.flush()

    async def revoke(
        self,
        *,
        auth_session: AuthSession,
    ) -> None:
        if auth_session.revoked_at is not None:
            return

        auth_session.revoked_at = datetime.now(UTC)

        await self.session.flush()

    async def revoke_family(
        self,
        *,
        family_id: uuid.UUID,
    ) -> int:
        now = datetime.now(UTC)

        result = await self.session.execute(
            update(AuthSession)
            .where(
                AuthSession.family_id == family_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=now,
            )
        )

        await self.session.flush()

        return result.rowcount or 0

    async def revoke_all_for_user(
        self,
        *,
        user_id: uuid.UUID,
    ) -> int:
        now = datetime.now(UTC)

        result = await self.session.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=now,
            )
        )

        await self.session.flush()

        return result.rowcount or 0
