from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel

from app.core.logging import logger
from app.schemas.base.mention import Mention
from app.schemas.base.movie import Movie as MovieBase
from app.service.post.schema.read_post_base import GetPostCountsStruct, GetPostStatusStruct
from app.service.redis.keys.post import (
    build_post_comment_count_redis_key,
    build_post_info_redis_key,
    build_post_liked_count_redis_key,
    build_post_saved_count_redis_key,
)
from app.service.redis.redis import redis_client

POST_CACHE_TTL_SECONDS = 3600


class CachedPostInfo(BaseModel):
    mentions: List[Mention] = []
    hashtags: List[str] = []
    movies: List[MovieBase] = []


class CachedPostStatus(BaseModel):
    is_liked: bool = False
    is_saved: bool = False
    is_following: bool = False


class PostCacheService:
    @staticmethod
    def _mget_raw(keys: List[str]) -> List[Optional[bytes]]:
        if not keys:
            return []
        return redis_client.redis_client.mget(keys)

    @staticmethod
    def _all_hit(values: List[Optional[bytes]]) -> bool:
        return bool(values) and all(value is not None for value in values)

    def get_infos(self, post_ids: List[int]) -> Tuple[Dict[int, CachedPostInfo], List[int]]:
        if not post_ids:
            return {}, []

        keys = [build_post_info_redis_key(post_id) for post_id in post_ids]
        try:
            values = self._mget_raw(keys)
        except Exception as e:
            logger.warning(f"[Redis Error] Post info cache read failed: {e}")
            return {}, post_ids

        if self._all_hit(values):
            return {
                post_id: CachedPostInfo.model_validate_json(values[index])
                for index, post_id in enumerate(post_ids)
            }, []

        cached: Dict[int, CachedPostInfo] = {}
        miss_ids: List[int] = []
        for index, post_id in enumerate(post_ids):
            value = values[index]
            if value is None:
                miss_ids.append(post_id)
                continue
            try:
                cached[post_id] = CachedPostInfo.model_validate_json(value)
            except Exception:
                miss_ids.append(post_id)
        return cached, miss_ids

    def set_infos(self, infos: Dict[int, CachedPostInfo]) -> None:
        if not infos:
            return

        try:
            redis_client.setex_many(
                {
                    build_post_info_redis_key(post_id): info.model_dump(mode="json")
                    for post_id, info in infos.items()
                },
                POST_CACHE_TTL_SECONDS,
            )
        except Exception as e:
            logger.warning(f"[Redis Error] Post info cache write failed: {e}")

    def get_counts(self, post_ids: List[int]) -> Tuple[Dict[int, GetPostCountsStruct], List[int]]:
        if not post_ids:
            return {}, []

        like_keys = [build_post_liked_count_redis_key(post_id) for post_id in post_ids]
        comment_keys = [build_post_comment_count_redis_key(post_id) for post_id in post_ids]
        try:
            like_values = self._mget_raw(like_keys)
            comment_values = self._mget_raw(comment_keys)
        except Exception as e:
            logger.warning(f"[Redis Error] Post count cache read failed: {e}")
            return {}, post_ids

        if self._all_hit(like_values) and self._all_hit(comment_values):
            return {
                post_id: GetPostCountsStruct(
                    like_count=int(like_values[index]),
                    comment_count=int(comment_values[index]),
                )
                for index, post_id in enumerate(post_ids)
            }, []

        cached: Dict[int, GetPostCountsStruct] = {}
        miss_ids: List[int] = []
        for index, post_id in enumerate(post_ids):
            if like_values[index] is None or comment_values[index] is None:
                miss_ids.append(post_id)
                continue
            cached[post_id] = GetPostCountsStruct(
                like_count=int(like_values[index]),
                comment_count=int(comment_values[index]),
            )
        return cached, miss_ids

    def set_counts(self, counts: Dict[int, GetPostCountsStruct]) -> None:
        if not counts:
            return

        payload: Dict[str, str] = {}
        for post_id, count in counts.items():
            payload[build_post_liked_count_redis_key(post_id)] = str(count["like_count"] or 0)
            payload[build_post_comment_count_redis_key(post_id)] = str(count["comment_count"] or 0)

        try:
            redis_client.setex_many(payload, POST_CACHE_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"[Redis Error] Post count cache write failed: {e}")

    def get_statuses(
        self, post_ids: List[int], user_id: UUID
    ) -> Tuple[Dict[int, CachedPostStatus], List[int]]:
        if not post_ids:
            return {}, []

        keys = [build_post_saved_count_redis_key(post_id, user_id) for post_id in post_ids]
        try:
            values = self._mget_raw(keys)
        except Exception as e:
            logger.warning(f"[Redis Error] Post status cache read failed: {e}")
            return {}, post_ids

        if self._all_hit(values):
            return {
                post_id: CachedPostStatus.model_validate_json(values[index])
                for index, post_id in enumerate(post_ids)
            }, []

        cached: Dict[int, CachedPostStatus] = {}
        miss_ids: List[int] = []
        for index, post_id in enumerate(post_ids):
            value = values[index]
            if value is None:
                miss_ids.append(post_id)
                continue
            try:
                cached[post_id] = CachedPostStatus.model_validate_json(value)
            except Exception:
                miss_ids.append(post_id)
        return cached, miss_ids

    def set_statuses(self, user_id: UUID, statuses: Dict[int, GetPostStatusStruct]) -> None:
        if not statuses:
            return

        try:
            redis_client.setex_many(
                {
                    build_post_saved_count_redis_key(post_id, user_id): CachedPostStatus(
                        is_liked=status["is_liked"],
                        is_saved=status["is_saved"],
                        is_following=status.get("is_following", False),
                    ).model_dump(mode="json")
                    for post_id, status in statuses.items()
                },
                POST_CACHE_TTL_SECONDS,
            )
        except Exception as e:
            logger.warning(f"[Redis Error] Post status cache write failed: {e}")

    def invalidate_post(self, post_id: int) -> None:
        keys = [
            build_post_info_redis_key(post_id),
            build_post_liked_count_redis_key(post_id),
            build_post_comment_count_redis_key(post_id),
        ]
        try:
            redis_client.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"[Redis Error] Post cache invalidate failed for {post_id}: {e}")

    def sync_comment_count(self, post_id: int, delta: int) -> None:
        if delta == 0:
            return

        key = build_post_comment_count_redis_key(post_id)
        try:
            if redis_client.redis_client.get(key) is None:
                self.invalidate_post(post_id)
                return
            if delta > 0:
                redis_client.increment_by(key, delta)
            else:
                new_count = redis_client.decrement_by(key, abs(delta))
                if new_count < 0:
                    redis_client.set(key, "0", ex=POST_CACHE_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"[Redis Error] Post comment_count sync failed for {post_id}: {e}")


post_cache_service = PostCacheService()

# backward compatibility
POST_INFO_CACHE_TTL_SECONDS = POST_CACHE_TTL_SECONDS
post_info_cache = post_cache_service
