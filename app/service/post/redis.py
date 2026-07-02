from pydantic import BaseModel

from app.service.redis.post_cache import (
    POST_INFO_CACHE_TTL_SECONDS,
    CachedPostInfo,
    PostInfoCacheService,
    post_info_cache,
)
from app.service.redis.keys.post import (
    build_post_comment_count_redis_key,
    build_post_info_redis_key,
    build_post_liked_count_redis_key,
    build_post_saved_count_redis_key,
)


class CachedPostSavedStatus(BaseModel):
    is_saved: bool = False
    is_liked: bool = False


class PostCacheService(PostInfoCacheService):
    pass


post_cache_service = post_info_cache

__all__ = [
    "POST_INFO_CACHE_TTL_SECONDS",
    "CachedPostInfo",
    "CachedPostSavedStatus",
    "PostCacheService",
    "post_cache_service",
    "build_post_info_redis_key",
    "build_post_liked_count_redis_key",
    "build_post_comment_count_redis_key",
    "build_post_saved_count_redis_key",
]
