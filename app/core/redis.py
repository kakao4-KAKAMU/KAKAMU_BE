import redis.asyncio as redis
from app.core.config import settings

# Redis URL 설정 (이미 노출된 암호는 settings.REDIS_URL 등에 넣어서 관리하세요)
redis_client = redis.from_url(
    settings.REDIS_URL, 
    decode_responses=True,
    encoding="utf-8"
)