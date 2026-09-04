import hashlib
import hmac
import secrets

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.email.base import EmailProvider
from app.models.user import User
from app.repositories.user_repository import UserRepository


class EmailVerificationService:
    CODE_DIGITS = 6

    def __init__(
        self,
        *,
        session: AsyncSession,
        redis: Redis,
        email_provider: EmailProvider,
        verification_secret: str,
        code_expire_minutes: int,
        resend_cooldown_seconds: int,
        max_attempts: int,
    ):
        self.session = session
        self.redis = redis
        self.email_provider = email_provider

        self.verification_secret = verification_secret.encode("utf-8")

        self.code_expire_seconds = code_expire_minutes * 60

        self.resend_cooldown_seconds = resend_cooldown_seconds

        self.max_attempts = max_attempts

        self.user_repository = UserRepository(session)

    @staticmethod
    def _code_key(
        user_id: str,
    ) -> str:
        return f"auth:email-verification:{user_id}:code"

    @staticmethod
    def _attempts_key(
        user_id: str,
    ) -> str:
        return f"auth:email-verification:{user_id}:attempts"

    @staticmethod
    def _cooldown_key(
        user_id: str,
    ) -> str:
        return f"auth:email-verification:{user_id}:cooldown"

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
            self.verification_secret,
            message,
            hashlib.sha256,
        ).hexdigest()

    async def send_verification_code(
        self,
        *,
        user: User,
    ) -> None:
        if user.email_verified_at is not None:
            return

        user_id = str(user.id)

        cooldown_key = self._cooldown_key(user_id)

        # Atomic resend cooldown.
        cooldown_acquired = await self.redis.set(
            cooldown_key,
            "1",
            ex=self.resend_cooldown_seconds,
            nx=True,
        )

        if not cooldown_acquired:
            raise ValueError("Verification code recently sent")

        code = self._generate_code()

        code_digest = self._hash_code(
            user_id=user_id,
            code=code,
        )

        code_key = self._code_key(user_id)

        attempts_key = self._attempts_key(user_id)

        await self.redis.set(
            code_key,
            code_digest,
            ex=self.code_expire_seconds,
        )

        await self.redis.set(
            attempts_key,
            "0",
            ex=self.code_expire_seconds,
        )

        text_body = (
            "Your Mausam email verification "
            f"code is {code}.\n\n"
            f"This code expires in "
            f"{self.code_expire_seconds // 60} "
            "minutes.\n\n"
            "If you did not create a Mausam "
            "account, you can ignore this email."
        )

        html_body = f"""
        <html>
            <body>
                <h2>Verify your Mausam email</h2>

                <p>
                    Enter this verification code
                    in the Mausam app:
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
                    If you did not create a Mausam
                    account, you can ignore this
                    email.
                </p>
            </body>
        </html>
        """

        try:
            await self.email_provider.send_email(
                to_email=user.email,
                subject="Verify your Mausam email",
                text_body=text_body,
                html_body=html_body,
            )

        except Exception:
            # Do not leave the user stuck behind a
            # cooldown if email delivery itself failed.
            await self.redis.delete(
                code_key,
                attempts_key,
                cooldown_key,
            )

            raise

    async def resend(
        self,
        *,
        email: str,
    ) -> None:
        normalized_email = email.lower().strip()

        user = await self.user_repository.get_by_email(normalized_email)

        # Avoid revealing whether an account exists.
        if user is None:
            return

        # Also keep this operation idempotent for
        # already-verified users.
        if user.email_verified_at is not None:
            return

        await self.send_verification_code(user=user)

    async def verify(
        self,
        *,
        email: str,
        code: str,
    ) -> User:
        normalized_email = email.lower().strip()

        user = await self.user_repository.get_by_email(normalized_email)

        # Don't distinguish an unknown email from
        # an invalid code.
        if user is None:
            raise ValueError("Invalid or expired verification code")

        # Verification is idempotent.
        if user.email_verified_at is not None:
            return user

        user_id = str(user.id)

        code_key = self._code_key(user_id)

        attempts_key = self._attempts_key(user_id)

        stored_digest = await self.redis.get(code_key)

        if stored_digest is None:
            raise ValueError("Invalid or expired verification code")

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

            raise ValueError("Too many verification attempts")

        submitted_digest = self._hash_code(
            user_id=user_id,
            code=code,
        )

        if not hmac.compare_digest(
            stored_digest,
            submitted_digest,
        ):
            new_attempts = await self.redis.incr(attempts_key)

            # If the attempts key unexpectedly expired
            # independently, restore an expiry.
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

                raise ValueError("Too many verification attempts")

            raise ValueError("Invalid or expired verification code")

        await self.user_repository.mark_email_verified(user=user)

        await self.session.commit()

        await self.redis.delete(
            code_key,
            attempts_key,
            self._cooldown_key(user_id),
        )

        return user
