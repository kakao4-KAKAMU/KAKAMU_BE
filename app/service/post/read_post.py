import time
from uuid import UUID
from typing import Optional, Dict, List, Set, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from app.models import Post, LikeLog, SaveLog, Block, User
from app.schemas.mapper.post import PostMapper
from app.schemas.response.post import PostResponse, PostListResponse
from app.service.post.schema.read_post_base import GetPostInfoFullStruct
from app.service.post.query.select_post_new import (
    PostInfoQueryOptions,
    PostReadServiceNew,
)


class PostReadService:
    def __init__(self):
        self._block_cache: Dict[UUID, Tuple[float, Set[UUID]]] = {}
        self._cache_ttl = 60

    def _get_cached_blocked_user_ids(self, db: Session, user_id: Optional[UUID]) -> Set[UUID]:
        if not user_id:
            return set()

        now = time.time()

        if len(self._block_cache) > 10000:
            self._block_cache.clear()

        if user_id in self._block_cache:
            cached_time, block_set = self._block_cache[user_id]
            if now - cached_time < self._cache_ttl:
                return block_set

        blocked_by_me = db.query(Block.blocked_id).filter(Block.blocker_id == user_id).all()
        blocking_me = db.query(Block.blocker_id).filter(Block.blocked_id == user_id).all()

        block_set = {b[0] for b in blocked_by_me} | {b[0] for b in blocking_me}
        self._block_cache[user_id] = (now, block_set)
        return block_set

    def _fetch_full_post_infos(
        self,
        db: Session,
        current_user_id: Optional[UUID],
        *,
        filters: tuple = (),
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Tuple[Dict[int, GetPostInfoFullStruct], List[int]]:
        query_filters = list(filters)
        if cursor is not None:
            query_filters.append(Post.id < cursor)

        _, ordered_post_ids = PostReadServiceNew.get_post_info_by_ids(
            db,
            None,
            options=PostInfoQueryOptions(
                filters=tuple(query_filters),
                order_by=Post.id.desc(),
                limit=limit,
            ),
        )
        if not ordered_post_ids:
            return {}, []

        return PostReadServiceNew.build_post_infos(db, ordered_post_ids, current_user_id)

    def _to_post_list_response(
        self,
        info_map: Dict[int, GetPostInfoFullStruct],
        ordered_post_ids: List[int],
        limit: int,
    ) -> PostListResponse:
        items = PostMapper.to_post_responses(info_map, ordered_post_ids)
        next_cursor = items[-1].id if items else None
        return PostListResponse(items=items, next_cursor=next_cursor, has_next=len(items) == limit)

    def get_posts(
        self, db: Session, current_user_id: Optional[UUID], cursor: Optional[int], limit: int
    ) -> PostListResponse:
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        filters: list = [User.status == "ACTIVE"]
        if blocked_user_ids:
            filters.append(Post.user_id.notin_(blocked_user_ids))

        info_map, ordered_post_ids = self._fetch_full_post_infos(
            db, current_user_id, filters=tuple(filters), cursor=cursor, limit=limit
        )
        return self._to_post_list_response(info_map, ordered_post_ids, limit)

    def get_my_liked_posts(
        self, db: Session, current_user_id: UUID, cursor: Optional[int], limit: int
    ) -> PostListResponse:
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        liked_post_ids_subquery = select(LikeLog.target_id).where(
            LikeLog.user_id == current_user_id,
            LikeLog.target_type == "POST",
            LikeLog.is_active == 1,
        )

        filters: list = [
            Post.id.in_(liked_post_ids_subquery),
            User.status == "ACTIVE",
        ]
        if blocked_user_ids:
            filters.append(Post.user_id.notin_(blocked_user_ids))

        info_map, ordered_post_ids = self._fetch_full_post_infos(
            db, current_user_id, filters=tuple(filters), cursor=cursor, limit=limit
        )
        return self._to_post_list_response(info_map, ordered_post_ids, limit)

    def get_my_saved_posts(
        self, db: Session, current_user_id: UUID, cursor: Optional[int], limit: int
    ) -> PostListResponse:
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        saved_post_ids_subquery = select(SaveLog.target_id).where(
            SaveLog.user_id == current_user_id,
            SaveLog.target_type == "POST",
            SaveLog.is_active == 1,
        )

        filters: list = [
            Post.id.in_(saved_post_ids_subquery),
            User.status == "ACTIVE",
        ]
        if blocked_user_ids:
            filters.append(Post.user_id.notin_(blocked_user_ids))

        info_map, ordered_post_ids = self._fetch_full_post_infos(
            db, current_user_id, filters=tuple(filters), cursor=cursor, limit=limit
        )
        return self._to_post_list_response(info_map, ordered_post_ids, limit)

    def get_user_posts(
        self,
        db: Session,
        target_user_id: UUID,
        current_user_id: Optional[UUID],
        cursor: Optional[int],
        limit: int,
    ) -> PostListResponse:
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)
        if target_user_id in blocked_user_ids:
            return PostListResponse(items=[], next_cursor=None, has_next=False)

        info_map, ordered_post_ids = self._fetch_full_post_infos(
            db,
            current_user_id,
            filters=(Post.user_id == target_user_id, User.status == "ACTIVE"),
            cursor=cursor,
            limit=limit,
        )
        return self._to_post_list_response(info_map, ordered_post_ids, limit)

    def get_post_detail(
        self, db: Session, post_id: int, current_user_id: Optional[UUID]
    ) -> PostResponse:
        info_map, ordered_post_ids = PostReadServiceNew.build_post_infos(
            db,
            [post_id],
            current_user_id,
            options=PostInfoQueryOptions(filters=(Post.id == post_id,)),
        )

        if post_id not in info_map:
            raise HTTPException(
                status_code=404,
                detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."},
            )

        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)
        if info_map[post_id]["author"].id in blocked_user_ids:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN_BLOCKED_POST", "message": "차단된 사용자의 게시물입니다."},
            )

        return PostMapper.to_post_responses(info_map, ordered_post_ids)[0]

    def get_posts_by_ids(
        self,
        db: Session,
        post_ids: list[int],
        current_user_id: Optional[UUID],
    ) -> list[PostResponse]:
        if not post_ids:
            return []

        unique_ids = list(dict.fromkeys(post_ids))
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        filters: list = [User.status == "ACTIVE"]
        if blocked_user_ids:
            filters.append(Post.user_id.notin_(blocked_user_ids))

        info_map, ordered_post_ids = PostReadServiceNew.build_post_infos(
            db,
            unique_ids,
            current_user_id,
            options=PostInfoQueryOptions(filters=tuple(filters)),
        )

        return PostMapper.to_post_responses(info_map, ordered_post_ids)


post_read_service = PostReadService()
