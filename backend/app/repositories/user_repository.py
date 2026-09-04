import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self,
        user_id: uuid.UUID,
    ) -> User | None:

        result = await self.session.execute(select(User).where(User.id == user_id))

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:

        result = await self.session.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()

    async def create(
        self,
        user: User,
    ) -> User:

        self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def increment_auth_version(
        self,
        *,
        user: User,
    ) -> int:
        user.auth_version += 1

        await self.session.flush()

        return user.auth_version

    async def update_password_hash(
        self,
        *,
        user: User,
        password_hash: str,
    ) -> User:
        user.password_hash = password_hash

        await self.session.flush()

        return user

    async def mark_email_verified(
        self,
        *,
        user: User,
    ) -> User:
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)
            await self.session.flush()

        return user
