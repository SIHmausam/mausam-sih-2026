import re
import uuid
from datetime import UTC, datetime

import pytest

from app.integrations.email.base import EmailProvider
from app.models.user import User
from app.services.email_verification_service import (
    EmailVerificationService,
)


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
        # Expiration timing itself is handled by
        # Redis in production.
        #
        # These unit tests manually remove keys
        # whenever expiry needs to be simulated.
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

    async def mark_email_verified(
        self,
        *,
        user: User,
    ) -> User:
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)

        return user


def create_user(
    *,
    email: str = "raman@example.com",
    verified: bool = False,
) -> User:
    return User(
        id=uuid.uuid4(),
        name="Raman",
        email=email,
        password_hash="hashed-password",
        is_active=True,
        auth_version=1,
        email_verified_at=(datetime.now(UTC) if verified else None),
    )


def build_service(
    *,
    user: User | None = None,
    email_provider: EmailProvider | None = None,
) -> tuple[
    EmailVerificationService,
    FakeSession,
    FakeRedis,
    EmailProvider,
]:
    session = FakeSession()
    redis = FakeRedis()

    provider = email_provider if email_provider is not None else FakeEmailProvider()

    service = EmailVerificationService(
        session=session,  # type: ignore[arg-type]
        redis=redis,  # type: ignore[arg-type]
        email_provider=provider,
        verification_secret=("test-email-verification-secret"),
        code_expire_minutes=15,
        resend_cooldown_seconds=60,
        max_attempts=5,
    )

    users = []

    if user is not None:
        users.append(user)

    service.user_repository = (
        FakeUserRepository(users)  # type: ignore[assignment]
    )

    return (
        service,
        session,
        redis,
        provider,
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


@pytest.mark.asyncio
async def test_verification_code_generated_and_email_sent():
    user = create_user()

    (
        service,
        _session,
        _redis,
        provider,
    ) = build_service(
        user=user,
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.send_verification_code(user=user)

    assert len(provider.messages) == 1

    message = provider.messages[0]

    assert message["to_email"] == user.email

    assert message["subject"] == ("Verify your Mausam email")

    code = extract_code(provider)

    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.asyncio
async def test_raw_code_is_not_stored_in_redis():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
    ) = build_service(
        user=user,
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.send_verification_code(user=user)

    code = extract_code(provider)

    code_key = f"auth:email-verification:{user.id}:code"

    stored_value = redis.storage[code_key]

    assert stored_value != code

    # SHA-256 HMAC hexadecimal digest.
    assert len(stored_value) == 64

    assert code not in redis.storage.values()


@pytest.mark.asyncio
async def test_correct_code_verifies_user():
    user = create_user()

    (
        service,
        session,
        redis,
        provider,
    ) = build_service(
        user=user,
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.send_verification_code(user=user)

    code = extract_code(provider)

    result = await service.verify(
        email=user.email,
        code=code,
    )

    assert result is user

    assert user.email_verified_at is not None

    assert session.commit_count == 1

    code_key = f"auth:email-verification:{user.id}:code"

    attempts_key = f"auth:email-verification:{user.id}:attempts"

    cooldown_key = f"auth:email-verification:{user.id}:cooldown"

    assert code_key not in redis.storage

    assert attempts_key not in redis.storage

    assert cooldown_key not in redis.storage


@pytest.mark.asyncio
async def test_wrong_code_is_rejected():
    user = create_user()

    (
        service,
        _session,
        redis,
        _provider,
    ) = build_service(
        user=user,
    )

    await service.send_verification_code(user=user)

    with pytest.raises(
        ValueError,
        match=("Invalid or expired verification code"),
    ):
        await service.verify(
            email=user.email,
            code="999999",
        )

    assert user.email_verified_at is None

    attempts_key = f"auth:email-verification:{user.id}:attempts"

    assert redis.storage[attempts_key] == "1"


@pytest.mark.asyncio
async def test_expired_or_missing_code_is_rejected():
    user = create_user()

    (
        service,
        _session,
        redis,
        _provider,
    ) = build_service(
        user=user,
    )

    await service.send_verification_code(user=user)

    code_key = f"auth:email-verification:{user.id}:code"

    # Simulate Redis TTL expiry.
    await redis.delete(code_key)

    with pytest.raises(
        ValueError,
        match=("Invalid or expired verification code"),
    ):
        await service.verify(
            email=user.email,
            code="123456",
        )

    assert user.email_verified_at is None


@pytest.mark.asyncio
async def test_five_wrong_attempts_invalidate_code():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
    ) = build_service(
        user=user,
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.send_verification_code(user=user)

    correct_code = extract_code(provider)

    wrong_code = "000000" if correct_code != "000000" else "999999"

    for _ in range(4):
        with pytest.raises(
            ValueError,
            match=("Invalid or expired verification code"),
        ):
            await service.verify(
                email=user.email,
                code=wrong_code,
            )

    with pytest.raises(
        ValueError,
        match=("Too many verification attempts"),
    ):
        await service.verify(
            email=user.email,
            code=wrong_code,
        )

    code_key = f"auth:email-verification:{user.id}:code"

    attempts_key = f"auth:email-verification:{user.id}:attempts"

    assert code_key not in redis.storage

    assert attempts_key not in redis.storage

    # Even the previously correct OTP can no
    # longer be used after the attempt limit.
    with pytest.raises(
        ValueError,
        match=("Invalid or expired verification code"),
    ):
        await service.verify(
            email=user.email,
            code=correct_code,
        )


@pytest.mark.asyncio
async def test_resend_within_cooldown_is_rejected():
    user = create_user()

    (
        service,
        _session,
        _redis,
        provider,
    ) = build_service(
        user=user,
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.send_verification_code(user=user)

    with pytest.raises(
        ValueError,
        match=("Verification code recently sent"),
    ):
        await service.resend(email=user.email)

    # No second email was sent.
    assert len(provider.messages) == 1


@pytest.mark.asyncio
async def test_resend_after_cooldown_works():
    user = create_user()

    (
        service,
        _session,
        redis,
        provider,
    ) = build_service(
        user=user,
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    await service.send_verification_code(user=user)

    first_code = extract_code(provider)

    cooldown_key = f"auth:email-verification:{user.id}:cooldown"

    # Simulate Redis cooldown expiry.
    await redis.delete(cooldown_key)

    await service.resend(email=user.email)

    assert len(provider.messages) == 2

    second_code = extract_code(provider)

    assert len(second_code) == 6

    # Codes are random. They will almost always
    # differ, but equality is technically possible,
    # so don't assert inequality here.
    assert first_code.isdigit()
    assert second_code.isdigit()


@pytest.mark.asyncio
async def test_already_verified_user_is_idempotent():
    user = create_user(verified=True)

    original_verified_at = user.email_verified_at

    (
        service,
        session,
        _redis,
        provider,
    ) = build_service(
        user=user,
    )

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    # Sending verification again should do
    # nothing for an already verified user.
    await service.send_verification_code(user=user)

    assert provider.messages == []

    # Verify should also simply return the user.
    result = await service.verify(
        email=user.email,
        code="123456",
    )

    assert result is user

    assert user.email_verified_at == original_verified_at

    assert session.commit_count == 0


@pytest.mark.asyncio
async def test_unknown_resend_email_does_not_reveal_account():
    (
        service,
        _session,
        _redis,
        provider,
    ) = build_service()

    assert isinstance(
        provider,
        FakeEmailProvider,
    )

    # Must not raise "user not found".
    await service.resend(email="unknown@example.com")

    assert provider.messages == []


@pytest.mark.asyncio
async def test_email_provider_failure_removes_verification_state():
    user = create_user()

    provider = FailingEmailProvider()

    (
        service,
        _session,
        redis,
        _provider,
    ) = build_service(
        user=user,
        email_provider=provider,
    )

    with pytest.raises(
        RuntimeError,
        match="SMTP delivery failed",
    ):
        await service.send_verification_code(user=user)

    code_key = f"auth:email-verification:{user.id}:code"

    attempts_key = f"auth:email-verification:{user.id}:attempts"

    cooldown_key = f"auth:email-verification:{user.id}:cooldown"

    assert code_key not in redis.storage

    assert attempts_key not in redis.storage

    assert cooldown_key not in redis.storage
