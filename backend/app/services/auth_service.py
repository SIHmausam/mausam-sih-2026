from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:

    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def register(
        self,
        name: str,
        email: str,
        password: str,
    ) -> User:

        email = email.lower().strip()

        existing_user = await self.repository.get_by_email(
            email
        )

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
    ) -> str:

        email = email.lower().strip()

        user = await self.repository.get_by_email(
            email
        )

        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise ValueError("Invalid credentials")

        return create_access_token(
            str(user.id)
        )