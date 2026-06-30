import json
from typing import Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.redis import sync_redis_client
from app.models import Comment, Hashtag, PostHashtag, PostMention, User
from app.schemas.base.mention import Mention

POST_INFO_CACHE_TTL_SECONDS = 3600


def build_post_info_redis_key(post_id: int) -> str:
    return f"kakamu:post:{post_id}:info"


class CachedPostInfo(BaseModel):
    mentions: List[Mention] = []
    hashtags: List[str] = []
    comment_count: int = 0


class PostCacheService:
    def get_post_infos(self, post_ids: List[int]) -> Dict[int, Optional[CachedPostInfo]]:
        if not post_ids:
            return {}

        keys = [build_post_info_redis_key(post_id) for post_id in post_ids]
        try:
            values = sync_redis_client.mget(keys)
        except Exception as e:
            logger.warning(f"[Redis Error] Post info cache read failed: {e}")
            return {post_id: None for post_id in post_ids}

        result: Dict[int, Optional[CachedPostInfo]] = {}
        for post_id, value in zip(post_ids, values):
            if value is None:
                result[post_id] = None
                continue
            try:
                result[post_id] = CachedPostInfo.model_validate(json.loads(value))
            except Exception as e:
                logger.warning(f"[Redis Error] Post info cache decode failed for {post_id}: {e}")
                result[post_id] = None
        return result

    def set_post_infos(self, infos: Dict[int, CachedPostInfo]) -> None:
        if not infos:
            return

        try:
            pipe = sync_redis_client.pipeline()
            for post_id, info in infos.items():
                pipe.setex(
                    build_post_info_redis_key(post_id),
                    POST_INFO_CACHE_TTL_SECONDS,
                    json.dumps(info.model_dump(mode="json")),
                )
            pipe.execute()
        except Exception as e:
            logger.warning(f"[Redis Error] Post info cache write failed: {e}")

    def invalidate_post(self, post_id: int) -> None:
        try:
            sync_redis_client.delete(build_post_info_redis_key(post_id))
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

        try:
            key = build_post_info_redis_key(post_id)
            cached = sync_redis_client.get(key)

            if cached is None:
                self._populate_post_info_from_db(db, post_id)
                return

            info = CachedPostInfo.model_validate(json.loads(cached))
            info.comment_count = max(0, info.comment_count + delta)
            sync_redis_client.setex(
                key,
                POST_INFO_CACHE_TTL_SECONDS,
                json.dumps(info.model_dump(mode="json")),
            )
        except Exception as e:
            logger.warning(f"[Redis Error] Post comment_count sync failed for {post_id}: {e}")


post_cache_service = PostCacheService()
