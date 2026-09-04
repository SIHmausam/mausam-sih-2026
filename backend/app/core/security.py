import uuid
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    *,
    session_id: str | None = None,
    auth_version: int | None = None,
) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": subject,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }

    if session_id is not None:
        payload["sid"] = session_id

    if auth_version is not None:
        payload["av"] = auth_version

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def create_refresh_token(
    subject: str,
    *,
    session_id: str | None = None,
    family_id: str | None = None,
    auth_version: int | None = None,
) -> tuple[str, str, datetime]:
    jti = str(uuid.uuid4())

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": jti,
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }

    if session_id is not None:
        payload["sid"] = session_id

    if family_id is not None:
        payload["family"] = family_id

    if auth_version is not None:
        payload["av"] = auth_version

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    return token, jti, expires_at


def decode_token(
    token: str,
) -> dict:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ALGORITHM],
    )
