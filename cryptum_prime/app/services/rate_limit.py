from datetime import datetime, timedelta

import redis.asyncio as redis

from app.core.config import get_settings


class RateLimiter:
    def __init__(self) -> None:
        settings = get_settings()
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)
        self.limit = settings.rate_limit_per_min

    async def allow(self, key: str) -> bool:
        now = datetime.utcnow()
        window = now.replace(second=0, microsecond=0)
        redis_key = f"rate:{key}:{window.isoformat()}"
        current = await self.redis.incr(redis_key)
        if current == 1:
            await self.redis.expire(redis_key, 60)
        return current <= self.limit

    async def close(self) -> None:
        await self.redis.close()
