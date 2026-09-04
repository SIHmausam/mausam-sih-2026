import re
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.security import (
    hash_password,
    verify_password,
)
from app.integrations.email.base import EmailProvider
from app.models.user import User
from app.services.password_reset_service import (
    PasswordResetService,
)

# ============================================================
# FAKES
# ============================================================


class FakeSession:
    def __init__(self) -> None:
        self.commit_count = 0

    async def commit(self) -> None:
        self.commit_count += 1


class FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def get(
        self,
        key: str,
    ) -> str | None:
        return self.storage.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool:
        if nx and key in self.storage:
            return False

        self.storage[key] = value
        return True

    async def delete(
        self,
        *keys: str,
    ) -> int:
        deleted = 0

        for key in keys:
            if key in self.storage:
                del self.storage[key]
                deleted += 1

        return deleted

    async def incr(
        self,
        key: str,
    ) -> int:
        current = int(
            self.storage.get(
                key,
                "0",
            )
        )

        current += 1

        self.storage[key] = str(current)

        return current

    async def expire(
        self,
        key: str,
        seconds: int,
    ) -> bool:
        return key in self.storage


class FakeEmailProvider(EmailProvider):
    def __init__(self) -> None:
        self.messages: list[dict[str, str | None]] = []

    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        self.messages.append(
            {
                "to_email": to_email,
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
            }
        )


class FailingEmailProvider(EmailProvider):
    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        raise RuntimeError("SMTP delivery failed")


class FakeUserRepository:
    def __init__(
        self,
        users: list[User],
    ) -> None:
        self.users = {user.email.lower(): user for user in users}

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        return self.users.get(email.lower())

    async def update_password_hash(
        self,
        *,
        user: User,
        password_hash: str,
    ) -> User:
        user.password_hash = password_hash

        return user

    async def increment_auth_version(
        self,
        *,
        user: User,
    ) -> int:
        user.auth_version += 1

        return user.auth_version


class FakeAuthSessionRepository:
    def __init__(
        self,
        sessions: list[SimpleNamespace] | None = None,
    ) -> None:
        self.sessions = sessions or []

        self.revoked_user_ids: list[uuid.UUID] = []

    async def list_active_for_user(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[SimpleNamespace]:
        return [
            session
            for session in self.sessions
            if (session.user_id == user_id and session.revoked_at is None)
        ]

    async def revoke_all_for_user(
        self,
        *,
        user_id: uuid.UUID,
    ) -> int:
        count = 0

        for session in self.sessions:
            if session.user_id == user_id and session.revoked_at is None:
                session.revoked_at = datetime.now(UTC)
                count += 1

        self.revoked_user_ids.append(user_id)

        return count


class FakeTokenService:
    def __init__(self) -> None:
        self.revoked_families: list[str] = []

    async def revoke_refresh_family(
        self,
        *,
        family_id: str,
        expires_at: datetime,
    ) -> None:
        self.revoked_families.append(family_id)


# ============================================================
# HELPERS
# ============================================================


def create_user(
    *,
    email: str = "raman@example.com",
    password: str = "OldPassword123",
    active: bool = True,
) -> User:
    return User(
        id=uuid.uuid4(),
        name="Raman",
        email=email,
        password_hash=hash_password(password),
        is_active=active,
        email_verified_at=datetime.now(UTC),
        auth_version=1,
    )


def create_auth_session(
    *,
    user_id: uuid.UUID,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        family_id=uuid.uuid4(),
        expires_at=(datetime.now(UTC) + timedelta(days=30)),
        revoked_at=None,
    )


def build_service(
    *,
    user: User | None = None,
    sessions: list[SimpleNamespace] | None = None,
    email_provider: (EmailProvider | None) = None,
) -> tuple[
    PasswordResetService,
    FakeSession,
    FakeRedis,
    EmailProvider,
    FakeAuthSessionRepository,
    FakeTokenService,
]:
    session = FakeSession()
    redis = FakeRedis()

    provider = email_provider if email_provider is not None else FakeEmailProvider()

    service = PasswordResetService(
        session=session,  # type: ignore[arg-type]
        redis=redis,  # type: ignore[arg-type]
        email_provider=provider,
        reset_secret=("test-password-reset-secret"),
        code_expire_minutes=15,
        resend_cooldown_seconds=60,
        max_attempts=5,
    )

    users: list[User] = []

    if user is not None:
        users.append(user)

    user_repository = FakeUserRepository(users)

    auth_session_repository = FakeAuthSessionRepository(sessions)

    token_service = FakeTokenService()

    service.user_repository = user_repository  # type: ignore[assignment]

    service.auth_session_repository = auth_session_repository  # type: ignore[assignment]

    service.token_service = token_service  # type: ignore[assignment]

    return (
        service,
        session,
        redis,
        provider,
        auth_session_repository,
        token_service,
    )


def extract_code(
    provider: FakeEmailProvider,
) -> str:
    assert provider.messages

    text_body = provider.messages[-1]["text_body"]

    assert text_body is not None

    match = re.search(
        r"\b(\d{6})\b",
        text_body,
    )

    assert match is not None

    return match.group(1)


# ============================================================
# REQUEST RESET TESTS
# ============================================================


@pytest.mark.asyncio
async def test_reset_code_generated_and_email_sent():
    user = create_user()

    (
        service,
        _session,
        _redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    assert len(provider.messages) == 1

    message = provider.messages[0]

    assert message["to_email"] == user.email

    assert message["subject"] == ("Reset your Mausam password")

    code = extract_code(provider)

    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.asyncio
async def test_raw_reset_code_not_stored_in_redis():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    code = extract_code(provider)

    code_key = f"auth:password-reset:{user.id}:code"

    stored_value = redis.storage[code_key]

    assert stored_value != code

    # HMAC-SHA256 hex digest.
    assert len(stored_value) == 64

    assert code not in (redis.storage.values())


@pytest.mark.asyncio
async def test_unknown_email_does_not_reveal_account():
    (
        service,
        _session,
        _redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service()

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email="unknown@example.com")

    assert provider.messages == []


@pytest.mark.asyncio
async def test_inactive_user_does_not_receive_reset_email():
    user = create_user(active=False)

    (
        service,
        _session,
        _redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    assert provider.messages == []


@pytest.mark.asyncio
async def test_password_reset_cooldown_enforced():
    user = create_user()

    (
        service,
        _session,
        _redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    with pytest.raises(
        ValueError,
        match=("Password reset code recently sent"),
    ):
        await service.request_reset(email=user.email)

    assert len(provider.messages) == 1


@pytest.mark.asyncio
async def test_password_reset_after_cooldown_works():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    cooldown_key = f"auth:password-reset:{user.id}:cooldown"

    # Simulate Redis TTL expiry.
    await redis.delete(cooldown_key)

    await service.request_reset(email=user.email)

    assert len(provider.messages) == 2


# ============================================================
# INVALID CODE TESTS
# ============================================================


@pytest.mark.asyncio
async def test_wrong_password_reset_code_rejected():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    real_code = extract_code(provider)

    wrong_code = "000000" if real_code != "000000" else "999999"

    with pytest.raises(
        ValueError,
        match=("Invalid or expired password reset code"),
    ):
        await service.reset_password(
            email=user.email,
            code=wrong_code,
            new_password=("NewPassword123"),
        )

    attempts_key = f"auth:password-reset:{user.id}:attempts"

    assert redis.storage[attempts_key] == "1"


@pytest.mark.asyncio
async def test_missing_or_expired_reset_code_rejected():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    code = extract_code(provider)

    code_key = f"auth:password-reset:{user.id}:code"

    # Simulate Redis expiration.
    await redis.delete(code_key)

    with pytest.raises(
        ValueError,
        match=("Invalid or expired password reset code"),
    ):
        await service.reset_password(
            email=user.email,
            code=code,
            new_password=("NewPassword123"),
        )


@pytest.mark.asyncio
async def test_five_invalid_attempts_invalidate_reset_code():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    correct_code = extract_code(provider)

    wrong_code = "000000" if correct_code != "000000" else "999999"

    for _ in range(4):
        with pytest.raises(
            ValueError,
            match=("Invalid or expired password reset code"),
        ):
            await service.reset_password(
                email=user.email,
                code=wrong_code,
                new_password=("NewPassword123"),
            )

    with pytest.raises(
        ValueError,
        match=("Too many password reset attempts"),
    ):
        await service.reset_password(
            email=user.email,
            code=wrong_code,
            new_password=("NewPassword123"),
        )

    code_key = f"auth:password-reset:{user.id}:code"

    attempts_key = f"auth:password-reset:{user.id}:attempts"

    assert code_key not in (redis.storage)

    assert attempts_key not in (redis.storage)

    # Previously valid code should now
    # also be unusable.
    with pytest.raises(
        ValueError,
        match=("Invalid or expired password reset code"),
    ):
        await service.reset_password(
            email=user.email,
            code=correct_code,
            new_password=("NewPassword123"),
        )


# ============================================================
# SUCCESSFUL RESET TESTS
# ============================================================


@pytest.mark.asyncio
async def test_correct_code_changes_password():
    user = create_user(password="OldPassword123")

    (
        service,
        session,
        _redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    code = extract_code(provider)

    await service.reset_password(
        email=user.email,
        code=code,
        new_password="NewPassword123",
    )

    assert not verify_password(
        "OldPassword123",
        user.password_hash,
    )

    assert verify_password(
        "NewPassword123",
        user.password_hash,
    )

    assert session.commit_count == 1


@pytest.mark.asyncio
async def test_successful_reset_increments_auth_version():
    user = create_user()

    original_auth_version = user.auth_version

    (
        service,
        _session,
        _redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    code = extract_code(provider)

    await service.reset_password(
        email=user.email,
        code=code,
        new_password="NewPassword123",
    )

    assert user.auth_version == (original_auth_version + 1)


@pytest.mark.asyncio
async def test_successful_reset_revokes_all_database_sessions():
    user = create_user()

    session_one = create_auth_session(user_id=user.id)

    session_two = create_auth_session(user_id=user.id)

    (
        service,
        _session,
        _redis,
        provider,
        auth_sessions,
        _tokens,
    ) = build_service(
        user=user,
        sessions=[
            session_one,
            session_two,
        ],
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    code = extract_code(provider)

    await service.reset_password(
        email=user.email,
        code=code,
        new_password="NewPassword123",
    )

    assert session_one.revoked_at is not None

    assert session_two.revoked_at is not None

    assert user.id in (auth_sessions.revoked_user_ids)


@pytest.mark.asyncio
async def test_successful_reset_revokes_all_refresh_families():
    user = create_user()

    session_one = create_auth_session(user_id=user.id)

    session_two = create_auth_session(user_id=user.id)

    (
        service,
        _session,
        _redis,
        provider,
        _sessions,
        token_service,
    ) = build_service(
        user=user,
        sessions=[
            session_one,
            session_two,
        ],
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    code = extract_code(provider)

    await service.reset_password(
        email=user.email,
        code=code,
        new_password="NewPassword123",
    )

    assert set(token_service.revoked_families) == {
        str(session_one.family_id),
        str(session_two.family_id),
    }


@pytest.mark.asyncio
async def test_reset_code_is_single_use():
    user = create_user()

    (
        service,
        _session,
        _redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    code = extract_code(provider)

    await service.reset_password(
        email=user.email,
        code=code,
        new_password="NewPassword123",
    )

    with pytest.raises(
        ValueError,
        match=("Invalid or expired password reset code"),
    ):
        await service.reset_password(
            email=user.email,
            code=code,
            new_password=("AnotherPassword123"),
        )


@pytest.mark.asyncio
async def test_successful_reset_clears_redis_state():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
        _sessions,
        _tokens,
    ) = build_service(user=user)

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.request_reset(email=user.email)

    code = extract_code(provider)

    await service.reset_password(
        email=user.email,
        code=code,
        new_password="NewPassword123",
    )

    prefix = f"auth:password-reset:{user.id}"

    assert f"{prefix}:code" not in redis.storage

    assert f"{prefix}:attempts" not in redis.storage

    assert f"{prefix}:cooldown" not in redis.storage


# ============================================================
# EMAIL FAILURE
# ============================================================


@pytest.mark.asyncio
async def test_email_failure_removes_password_reset_state():
    user = create_user()

    provider = FailingEmailProvider()

    (
        service,
        _session,
        redis,
        _provider,
        _sessions,
        _tokens,
    ) = build_service(
        user=user,
        email_provider=provider,
    )

    with pytest.raises(
        RuntimeError,
        match="SMTP delivery failed",
    ):
        await service.request_reset(email=user.email)

    prefix = f"auth:password-reset:{user.id}"

    assert f"{prefix}:code" not in redis.storage

    assert f"{prefix}:attempts" not in redis.storage

    assert f"{prefix}:cooldown" not in redis.storage
