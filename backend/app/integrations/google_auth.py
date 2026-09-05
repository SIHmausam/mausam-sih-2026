import asyncio
from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2 import id_token


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str
    name: str
    email_verified: bool


class GoogleTokenVerifier:
    def __init__(
        self,
        *,
        allowed_client_ids: list[str],
    ):
        self.allowed_client_ids = [
            client_id for client_id in allowed_client_ids if client_id
        ]

        if not self.allowed_client_ids:
            raise ValueError("No Google OAuth client IDs configured")

    async def verify(
        self,
        token: str,
    ) -> GoogleIdentity:
        claims = await asyncio.to_thread(
            self._verify_sync,
            token,
        )

        subject = claims.get("sub")
        email = claims.get("email")
        name = claims.get("name") or email
        email_verified = bool(claims.get("email_verified"))

        if not subject or not email or not email_verified:
            raise ValueError("Invalid Google identity")

        return GoogleIdentity(
            subject=str(subject),
            email=str(email).lower().strip(),
            name=str(name),
            email_verified=True,
        )

    def _verify_sync(
        self,
        token: str,
    ) -> dict:
        request = Request()

        for client_id in self.allowed_client_ids:
            try:
                return id_token.verify_oauth2_token(
                    token,
                    request,
                    client_id,
                )
            except ValueError:
                continue

        raise ValueError("Invalid Google ID token")
