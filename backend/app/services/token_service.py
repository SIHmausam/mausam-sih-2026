from datetime import UTC, datetime

from redis.asyncio import Redis


class TokenService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def store_refresh_token(
        self,
        jti: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        ttl = int((expires_at - datetime.now(UTC)).total_seconds())

        if ttl <= 0:
            return

        await self.redis.set(
            f"refresh:{jti}",
            user_id,
            ex=ttl,
        )

    async def get_refresh_token_owner(
        self,
        jti: str,
    ) -> str | None:
        return await self.redis.get(f"refresh:{jti}")

    async def revoke_refresh_token(
        self,
        jti: str,
    ) -> None:
        await self.redis.delete(f"refresh:{jti}")
