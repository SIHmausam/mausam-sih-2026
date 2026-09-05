from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_identity import AuthIdentity


class AuthIdentityRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        identity: AuthIdentity,
    ) -> AuthIdentity:
        self.session.add(identity)

        await self.session.flush()

        return identity

    async def get_by_provider_subject(
        self,
        *,
        provider: str,
        provider_subject: str,
    ) -> AuthIdentity | None:
        result = await self.session.execute(
            select(AuthIdentity).where(
                AuthIdentity.provider == provider,
                AuthIdentity.provider_subject == provider_subject,
            )
        )

        return result.scalar_one_or_none()

    async def get_for_user_provider(
        self,
        *,
        user_id,
        provider: str,
    ) -> AuthIdentity | None:
        result = await self.session.execute(
            select(AuthIdentity).where(
                AuthIdentity.user_id == user_id,
                AuthIdentity.provider == provider,
            )
        )

        return result.scalar_one_or_none()
