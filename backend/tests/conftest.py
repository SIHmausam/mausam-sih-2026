import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

import app.models
from app.core.database import get_db_session
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.base import Base
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite://"


engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)


TestSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    async with TestSessionLocal() as db_session:
        yield db_session


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    test_user = User(
        id=uuid.uuid4(),
        name="Preference Test User",
        email=f"{uuid.uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    session.add(test_user)

    await session.commit()
    await session.refresh(test_user)

    return test_user


@pytest_asyncio.fixture
async def second_user(
    session: AsyncSession,
) -> User:
    test_user = User(
        id=uuid.uuid4(),
        name="Second Test User",
        email=f"{uuid.uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    session.add(test_user)

    await session.commit()
    await session.refresh(test_user)

    return test_user


@pytest_asyncio.fixture
async def client(
    user: User,
) -> AsyncGenerator[AsyncClient]:

    async def override_db_session():
        async with TestSessionLocal() as db_session:
            yield db_session

    async def override_current_user():
        return user

    app.dependency_overrides[get_db_session] = override_db_session

    app.dependency_overrides[get_current_user] = override_current_user

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()
