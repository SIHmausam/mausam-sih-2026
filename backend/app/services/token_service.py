import json
from datetime import UTC, datetime

from redis.asyncio import Redis


class TokenService:
    def __init__(
        self,
        redis: Redis,
    ):
        self.redis = redis

    @staticmethod
    def _ttl(
        expires_at: datetime,
    ) -> int:
        return max(
            1,
            int((expires_at - datetime.now(UTC)).total_seconds()),
        )

    async def store_session_refresh_token(
        self,
        *,
        jti: str,
        user_id: str,
        session_id: str,
        family_id: str,
        expires_at: datetime,
    ) -> None:
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "family_id": family_id,
        }

        await self.redis.set(
            f"refresh:active:{jti}",
            json.dumps(payload),
            ex=self._ttl(expires_at),
        )

    async def get_active_refresh_token(
        self,
        *,
        jti: str,
    ) -> dict[str, str] | None:
        raw = await self.redis.get(f"refresh:active:{jti}")

        if raw is None:
            return None

        if isinstance(raw, bytes):
            raw = raw.decode()

        return json.loads(raw)

    async def mark_refresh_token_consumed(
        self,
        *,
        jti: str,
        family_id: str,
        expires_at: datetime,
    ) -> None:
        await self.redis.delete(f"refresh:active:{jti}")

        await self.redis.set(
            f"refresh:consumed:{jti}",
            family_id,
            ex=self._ttl(expires_at),
        )

    async def is_refresh_token_consumed(
        self,
        *,
        jti: str,
    ) -> bool:
        return await self.redis.exists(f"refresh:consumed:{jti}") > 0

    async def revoke_refresh_family(
        self,
        *,
        family_id: str,
        expires_at: datetime,
    ) -> None:
        await self.redis.set(
            f"refresh:family:revoked:{family_id}",
            "1",
            ex=self._ttl(expires_at),
        )

    async def is_refresh_family_revoked(
        self,
        *,
        family_id: str,
    ) -> bool:
        return await self.redis.exists(f"refresh:family:revoked:{family_id}") > 0
