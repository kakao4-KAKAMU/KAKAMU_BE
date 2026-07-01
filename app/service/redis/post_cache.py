from typing import Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models import Comment, Hashtag, PostHashtag, PostMention, User
from app.schemas.base.mention import Mention
from app.service.redis.keys.post import build_post_info_redis_key
from app.service.redis.redis import redis_client

POST_INFO_CACHE_TTL_SECONDS = 3600


class CachedPostInfo(BaseModel):
    mentions: List[Mention] = []
    hashtags: List[str] = []
    like_count: int = 0
    comment_count: int = 0


class PostInfoCacheService:
    def get_post_infos(self, post_ids: List[int]) -> Dict[int, Optional[CachedPostInfo]]:
        if not post_ids:
            return {}

        keys = [build_post_info_redis_key(post_id) for post_id in post_ids]
        try:
            cached_by_key = redis_client.get_many(keys, CachedPostInfo)
        except Exception as e:
            logger.warning(f"[Redis Error] Post info cache read failed: {e}")
            return {post_id: None for post_id in post_ids}

        return {
            post_id: cached_by_key.get(build_post_info_redis_key(post_id))
            for post_id in post_ids
        }

    def set_post_infos(self, infos: Dict[int, CachedPostInfo]) -> None:
        if not infos:
            return

        try:
            redis_client.setex_many(
                {
                    build_post_info_redis_key(post_id): info.model_dump(mode="json")
                    for post_id, info in infos.items()
                },
                POST_INFO_CACHE_TTL_SECONDS,
            )
        except Exception as e:
            logger.warning(f"[Redis Error] Post info cache write failed: {e}")

    def invalidate_post(self, post_id: int) -> None:
        try:
            redis_client.delete(build_post_info_redis_key(post_id))
        except Exception as e:
            logger.warning(f"[Redis Error] Post info cache invalidate failed for {post_id}: {e}")

    def _populate_post_info_from_db(self, db: Session, post_id: int) -> None:
        mentions_query = (
            db.query(User.id, User.nickname, User.tag)
            .join(PostMention, PostMention.user_id == User.id)
            .filter(PostMention.post_id == post_id, User.status == "ACTIVE")
            .all()
        )
        mentions = [
            Mention(id=row.id, nickname=row.nickname, tag=row.tag)
            for row in mentions_query
        ]

        hashtags_query = (
            db.query(Hashtag.normalized_keyword)
            .join(PostHashtag, PostHashtag.hashtag_id == Hashtag.id)
            .filter(PostHashtag.post_id == post_id)
            .all()
        )
        hashtags = [row.normalized_keyword for row in hashtags_query]

        comment_count = (
            db.query(func.count(Comment.id))
            .filter(Comment.post_id == post_id, Comment.status == "ACTIVE")
            .scalar()
        ) or 0

        self.set_post_infos(
            {
                post_id: CachedPostInfo(
                    mentions=mentions,
                    hashtags=hashtags,
                    comment_count=comment_count,
                )
            }
        )

    def sync_comment_count(self, db: Session, post_id: int, delta: int) -> None:
        if delta == 0:
            return

        key = build_post_info_redis_key(post_id)
        try:
            cached = redis_client.get(key, CachedPostInfo)

            if cached is None:
                self._populate_post_info_from_db(db, post_id)
                return

            cached.comment_count = max(0, cached.comment_count + delta)
            redis_client.set(key, cached.model_dump(mode="json"), ex=POST_INFO_CACHE_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"[Redis Error] Post comment_count sync failed for {post_id}: {e}")


post_info_cache = PostInfoCacheService()
