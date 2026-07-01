import time
from dataclasses import dataclass
from uuid import UUID
from typing import Optional, Dict, List, Set, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from app.models import Post, LikeLog, SaveLog, Block, User
from app.schemas.base.mention import Mention
from app.schemas.base.movie import Movie
from app.schemas.mapper.post import PostMapper
from app.schemas.response.post import PostResponse, PostListResponse
from app.service.relation.relation_service import RelationService
from app.service.like.like_count_service import like_count_service
from app.service.post.redis import CachedPostInfo, post_cache_service
from app.service.post.read_post_new import PostInfoQueryOptions, PostReadServiceNew


@dataclass
class PostListContext:
    mentions_map: Dict[int, List[Mention]]
    hashtags_map: Dict[int, List[str]]
    comment_counts_map: Dict[int, int]
    like_counts_map: Dict[int, int]
    liked_post_ids: Set[int]
    saved_post_ids: Set[int]
    followed_user_ids: Set[UUID]


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

    @staticmethod
    def _posts_with_author_from_info(
        info_map: Dict[int, dict],
        ordered_post_ids: List[int],
    ) -> List[Tuple[Post, User]]:
        return [
            (info_map[post_id]["post"], info_map[post_id]["author"])
            for post_id in ordered_post_ids
            if post_id in info_map
        ]

    @staticmethod
    def _mentions_from_raw(raw_mentions: List[dict]) -> List[Mention]:
        return [Mention(**mention) for mention in raw_mentions]

    @staticmethod
    def _movies_map_from_info(info_map: Dict[int, dict]) -> Dict[int, List[Movie]]:
        return {
            post_id: [Movie(**movie) for movie in row.get("movies", [])]
            for post_id, row in info_map.items()
        }

    def _fetch_posts(
        self,
        db: Session,
        *,
        filters: tuple = (),
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
        post_ids: List[int] | None = None,
    ) -> Tuple[Dict[int, dict], List[int]]:
        query_filters = list(filters)
        if cursor is not None:
            query_filters.append(Post.id < cursor)

        info_map, ordered_post_ids = PostReadServiceNew.get_post_info_by_ids(
            db,
            post_ids,
            options=PostInfoQueryOptions(
                filters=tuple(query_filters),
                order_by=Post.id.desc(),
                limit=limit,
            ),
        )
        return info_map, ordered_post_ids

    def _build_post_infos(
        self,
        db: Session,
        posts: List[Post],
        current_user_id: Optional[UUID],
        info_map: Dict[int, dict] | None = None,
        *,
        force_liked: bool = False,
        force_saved: bool = False,
    ) -> PostListContext:
        post_ids = [post.id for post in posts]
        if not post_ids:
            return PostListContext({}, {}, {}, {}, set(), set(), set())

        cached_infos = post_cache_service.get_post_infos(post_ids)
        cache_miss_ids = [post_id for post_id in post_ids if cached_infos.get(post_id) is None]

        mentions_map: Dict[int, List[Mention]] = {}
        hashtags_map: Dict[int, List[str]] = {}
        comment_counts_map: Dict[int, int] = {}

        for post_id in post_ids:
            cached = cached_infos.get(post_id)
            if cached is not None:
                mentions_map[post_id] = cached.mentions
                hashtags_map[post_id] = cached.hashtags
                comment_counts_map[post_id] = cached.comment_count
            elif info_map and post_id in info_map:
                row = info_map[post_id]
                mentions_map[post_id] = self._mentions_from_raw(row.get("mentions", []))
                hashtags_map[post_id] = row.get("hashtags", [])

        if cache_miss_ids:
            db_info_map, _ = PostReadServiceNew.get_post_info_by_ids(db, cache_miss_ids)
            counts_map = PostReadServiceNew.get_post_counts_by_ids(db, cache_miss_ids)
            to_cache: Dict[int, CachedPostInfo] = {}

            for post_id in cache_miss_ids:
                row = db_info_map.get(post_id, {}) | counts_map.get(post_id, {})
                mentions = self._mentions_from_raw(row.get("mentions", []))
                hashtags = row.get("hashtags", [])
                comment_count = row.get("comment_count") or 0
                mentions_map[post_id] = mentions
                hashtags_map[post_id] = hashtags
                comment_counts_map[post_id] = comment_count
                to_cache[post_id] = CachedPostInfo(
                    mentions=mentions,
                    hashtags=hashtags,
                    comment_count=comment_count,
                )

            post_cache_service.set_post_infos(to_cache)

        for post_id in post_ids:
            comment_counts_map.setdefault(post_id, 0)
            mentions_map.setdefault(post_id, [])
            hashtags_map.setdefault(post_id, [])

        liked_post_ids: Set[int] = set()
        saved_post_ids: Set[int] = set()
        followed_user_ids: Set[UUID] = set()

        if current_user_id:
            if force_liked:
                liked_post_ids = set(post_ids)
            if force_saved:
                saved_post_ids = set(post_ids)

            if not (force_liked and force_saved):
                status_map = PostReadServiceNew.get_post_status_by_user_and_post_ids(
                    db, current_user_id, post_ids
                )
                if not force_liked:
                    liked_post_ids = {
                        post_id
                        for post_id in post_ids
                        if status_map.get(post_id, {}).get("is_liked", False)
                    }
                if not force_saved:
                    saved_post_ids = {
                        post_id
                        for post_id in post_ids
                        if status_map.get(post_id, {}).get("is_saved", False)
                    }

            author_user_ids = list({post.user_id for post in posts})
            followed_user_ids = RelationService.get_followed_user_ids(
                db, current_user_id, author_user_ids
            )

        return PostListContext(
            mentions_map=mentions_map,
            hashtags_map=hashtags_map,
            comment_counts_map=comment_counts_map,
            like_counts_map=like_count_service.resolve_like_counts(
                "POST",
                {post.id: post.like_count or 0 for post in posts},
            ),
            liked_post_ids=liked_post_ids,
            saved_post_ids=saved_post_ids,
            followed_user_ids=followed_user_ids,
        )

    def _build_post_list(
        self,
        posts_with_author: List[Tuple[Post, User]],
        *,
        context: PostListContext,
        limit: int,
        info_map: Dict[int, dict],
        force_liked: bool = False,
        force_saved: bool = False,
    ) -> PostListResponse:
        result = PostMapper.to_post_responses(
            posts_with_author,
            hashtags_map=context.hashtags_map,
            mentions_map=context.mentions_map,
            comment_counts_map=context.comment_counts_map,
            like_counts_map=context.like_counts_map,
            liked_post_ids=context.liked_post_ids,
            saved_post_ids=context.saved_post_ids,
            followed_user_ids=context.followed_user_ids,
            movies_map=self._movies_map_from_info(info_map),
            force_liked=force_liked,
            force_saved=force_saved,
        )

        next_cursor = result[-1].id if result else None
        return PostListResponse(items=result, next_cursor=next_cursor, has_next=len(result) == limit)

    def get_posts(
        self, db: Session, current_user_id: Optional[UUID], cursor: Optional[int], limit: int
    ) -> PostListResponse:
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        filters: list = [User.status == "ACTIVE"]
        if blocked_user_ids:
            filters.append(Post.user_id.notin_(blocked_user_ids))

        info_map, ordered_post_ids = self._fetch_posts(
            db,
            filters=tuple(filters),
            cursor=cursor,
            limit=limit,
        )
        posts_with_author = self._posts_with_author_from_info(info_map, ordered_post_ids)
        posts = [post for post, _ in posts_with_author]
        context = self._build_post_infos(db, posts, current_user_id, info_map)

        return self._build_post_list(
            posts_with_author,
            context=context,
            limit=limit,
            info_map=info_map,
        )

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

        info_map, ordered_post_ids = self._fetch_posts(
            db,
            filters=tuple(filters),
            cursor=cursor,
            limit=limit,
        )
        posts_with_author = self._posts_with_author_from_info(info_map, ordered_post_ids)
        posts = [post for post, _ in posts_with_author]
        context = self._build_post_infos(
            db, posts, current_user_id, info_map, force_liked=True
        )

        return self._build_post_list(
            posts_with_author,
            context=context,
            limit=limit,
            info_map=info_map,
            force_liked=True,
        )

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

        info_map, ordered_post_ids = self._fetch_posts(
            db,
            filters=tuple(filters),
            cursor=cursor,
            limit=limit,
        )
        posts_with_author = self._posts_with_author_from_info(info_map, ordered_post_ids)
        posts = [post for post, _ in posts_with_author]
        context = self._build_post_infos(
            db, posts, current_user_id, info_map, force_saved=True
        )

        return self._build_post_list(
            posts_with_author,
            context=context,
            limit=limit,
            info_map=info_map,
            force_saved=True,
        )

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

        info_map, ordered_post_ids = self._fetch_posts(
            db,
            filters=(Post.user_id == target_user_id, User.status == "ACTIVE"),
            cursor=cursor,
            limit=limit,
        )
        posts_with_author = self._posts_with_author_from_info(info_map, ordered_post_ids)
        posts = [post for post, _ in posts_with_author]
        context = self._build_post_infos(db, posts, current_user_id, info_map)

        return self._build_post_list(
            posts_with_author,
            context=context,
            limit=limit,
            info_map=info_map,
        )

    def get_post_detail(
        self, db: Session, post_id: int, current_user_id: Optional[UUID]
    ) -> PostResponse:
        info_map, _ = PostReadServiceNew.get_post_info_by_ids(
            db,
            [post_id],
        )

        if post_id not in info_map:
            raise HTTPException(
                status_code=404,
                detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."},
            )

        post = info_map[post_id]["post"]
        author = info_map[post_id]["author"]
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)
        if post.user_id in blocked_user_ids:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN_BLOCKED_POST", "message": "차단된 사용자의 게시물입니다."},
            )

        context = self._build_post_infos(db, [post], current_user_id, info_map)
        responses = PostMapper.to_post_responses(
            [(post, author)],
            hashtags_map=context.hashtags_map,
            mentions_map=context.mentions_map,
            comment_counts_map=context.comment_counts_map,
            like_counts_map=context.like_counts_map,
            liked_post_ids=context.liked_post_ids,
            saved_post_ids=context.saved_post_ids,
            followed_user_ids=context.followed_user_ids,
            movies_map=self._movies_map_from_info(info_map),
        )
        return responses[0]

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

        info_map, _ = PostReadServiceNew.get_post_info_by_ids(
            db,
            unique_ids,
            options=PostInfoQueryOptions(
                filters=tuple(filters),
            ),
        )

        posts_with_author = [
            (info_map[pid]["post"], info_map[pid]["author"])
            for pid in post_ids
            if pid in info_map
        ]
        posts = [post for post, _ in posts_with_author]
        context = self._build_post_infos(db, posts, current_user_id, info_map)

        return PostMapper.to_post_responses(
            posts_with_author,
            hashtags_map=context.hashtags_map,
            mentions_map=context.mentions_map,
            comment_counts_map=context.comment_counts_map,
            like_counts_map=context.like_counts_map,
            liked_post_ids=context.liked_post_ids,
            saved_post_ids=context.saved_post_ids,
            followed_user_ids=context.followed_user_ids,
            movies_map=self._movies_map_from_info(info_map),
        )


post_read_service = PostReadService()
