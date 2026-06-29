import redis
import redis.asyncio as aioredis
from app.core.config import settings
from typing import AsyncGenerator

# Redis URL 설정 (이미 노출된 암호는 settings.REDIS_URL 등에 넣어서 관리하세요)
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    encoding="utf-8",
)
sync_redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    encoding="utf-8",
)
# Redis 서버 관리
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    async with redis_client as client:
        yield client