import hashlib
import hmac
import secrets

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.integrations.email.base import EmailProvider
from app.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenService


class PasswordResetService:
    CODE_DIGITS = 6

    def __init__(
        self,
        *,
        session: AsyncSession,
        redis: Redis,
        email_provider: EmailProvider,
        reset_secret: str,
        code_expire_minutes: int,
        resend_cooldown_seconds: int,
        max_attempts: int,
    ):
        self.session = session
        self.redis = redis
        self.email_provider = email_provider

        self.reset_secret = reset_secret.encode("utf-8")

        self.code_expire_seconds = code_expire_minutes * 60

        self.resend_cooldown_seconds = resend_cooldown_seconds

        self.max_attempts = max_attempts

        self.user_repository = UserRepository(session)

        self.auth_session_repository = AuthSessionRepository(session)

        self.token_service = TokenService(redis)

    @staticmethod
    def _code_key(
        user_id: str,
    ) -> str:
        return f"auth:password-reset:{user_id}:code"

    @staticmethod
    def _attempts_key(
        user_id: str,
    ) -> str:
        return f"auth:password-reset:{user_id}:attempts"

    @staticmethod
    def _cooldown_key(
        user_id: str,
    ) -> str:
        return f"auth:password-reset:{user_id}:cooldown"

    @classmethod
    def _generate_code(
        cls,
    ) -> str:
        maximum = 10**cls.CODE_DIGITS

        code = secrets.randbelow(maximum)

        return str(code).zfill(cls.CODE_DIGITS)

    def _hash_code(
        self,
        *,
        user_id: str,
        code: str,
    ) -> str:
        message = (f"{user_id}:{code}").encode()

        return hmac.new(
            self.reset_secret,
            message,
            hashlib.sha256,
        ).hexdigest()

    async def request_reset(
        self,
        *,
        email: str,
    ) -> None:
        normalized_email = email.lower().strip()

        user = await self.user_repository.get_by_email(normalized_email)

        # Prevent account enumeration.
        if user is None:
            return

        if not user.is_active:
            return

        user_id = str(user.id)

        cooldown_key = self._cooldown_key(user_id)

        cooldown_acquired = await self.redis.set(
            cooldown_key,
            "1",
            ex=(self.resend_cooldown_seconds),
            nx=True,
        )

        if not cooldown_acquired:
            raise ValueError("Password reset code recently sent")

        code = self._generate_code()

        digest = self._hash_code(
            user_id=user_id,
            code=code,
        )

        code_key = self._code_key(user_id)

        attempts_key = self._attempts_key(user_id)

        await self.redis.set(
            code_key,
            digest,
            ex=self.code_expire_seconds,
        )

        await self.redis.set(
            attempts_key,
            "0",
            ex=self.code_expire_seconds,
        )

        text_body = (
            "Your Mausam password reset "
            f"code is {code}.\n\n"
            "This code expires in "
            f"{self.code_expire_seconds // 60} "
            "minutes.\n\n"
            "If you did not request a password "
            "reset, you can ignore this email."
        )

        html_body = f"""
        <html>
            <body>
                <h2>Reset your Mausam password</h2>

                <p>
                    Enter this code in the
                    Mausam app:
                </p>

                <p style="
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 6px;
                ">
                    {code}
                </p>

                <p>
                    This code expires in
                    {self.code_expire_seconds // 60}
                    minutes.
                </p>

                <p>
                    If you did not request this
                    password reset, you can ignore
                    this email.
                </p>
            </body>
        </html>
        """

        try:
            await self.email_provider.send_email(
                to_email=user.email,
                subject=("Reset your Mausam password"),
                text_body=text_body,
                html_body=html_body,
            )

        except Exception:
            await self.redis.delete(
                code_key,
                attempts_key,
                cooldown_key,
            )

            raise

    async def reset_password(
        self,
        *,
        email: str,
        code: str,
        new_password: str,
    ) -> None:
        normalized_email = email.lower().strip()

        user = await self.user_repository.get_by_email(normalized_email)

        if user is None:
            raise ValueError("Invalid or expired password reset code")

        if not user.is_active:
            raise ValueError("Invalid or expired password reset code")

        user_id = str(user.id)

        code_key = self._code_key(user_id)

        attempts_key = self._attempts_key(user_id)

        stored_digest = await self.redis.get(code_key)

        if stored_digest is None:
            raise ValueError("Invalid or expired password reset code")

        if isinstance(
            stored_digest,
            bytes,
        ):
            stored_digest = stored_digest.decode("utf-8")

        raw_attempts = await self.redis.get(attempts_key)

        if isinstance(
            raw_attempts,
            bytes,
        ):
            raw_attempts = raw_attempts.decode("utf-8")

        attempts = int(raw_attempts) if raw_attempts is not None else 0

        if attempts >= self.max_attempts:
            await self.redis.delete(
                code_key,
                attempts_key,
            )

            raise ValueError("Too many password reset attempts")

        submitted_digest = self._hash_code(
            user_id=user_id,
            code=code,
        )

        if not hmac.compare_digest(
            stored_digest,
            submitted_digest,
        ):
            new_attempts = await self.redis.incr(attempts_key)

            if new_attempts == 1:
                await self.redis.expire(
                    attempts_key,
                    self.code_expire_seconds,
                )

            if new_attempts >= self.max_attempts:
                await self.redis.delete(
                    code_key,
                    attempts_key,
                )

                raise ValueError("Too many password reset attempts")

            raise ValueError("Invalid or expired password reset code")

        active_sessions = await self.auth_session_repository.list_active_for_user(
            user_id=user.id
        )

        # Revoke every refresh family first.
        for auth_session in active_sessions:
            await self.token_service.revoke_refresh_family(
                family_id=str(auth_session.family_id),
                expires_at=(auth_session.expires_at),
            )

        # Revoke every DB session.
        await self.auth_session_repository.revoke_all_for_user(user_id=user.id)

        # Replace password hash.
        await self.user_repository.update_password_hash(
            user=user,
            password_hash=(hash_password(new_password)),
        )

        # Invalidates ALL previously issued
        # access and refresh JWTs.
        await self.user_repository.increment_auth_version(user=user)

        await self.session.commit()

        # Reset code is single use.
        await self.redis.delete(
            code_key,
            attempts_key,
            self._cooldown_key(user_id),
        )
