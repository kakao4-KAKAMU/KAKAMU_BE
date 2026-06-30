import time
from dataclasses import dataclass
from uuid import UUID
from typing import Optional, Dict, List, Set, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, select
from fastapi import HTTPException

from app.models import Post, Hashtag, PostHashtag, Comment, LikeLog, Block, User, PostMention, Follow, Movie
from app.schemas.base.mention import Mention
from app.schemas.mapper.post import PostMapper
from app.schemas.response.post import PostResponse, PostListResponse
from app.service.relation.relation_service import RelationService
from app.service.like.like_count_service import like_count_service
from app.service.post.redis import CachedPostInfo, post_cache_service


@dataclass
class PostListContext:
    mentions_map: Dict[int, List[Mention]]
    hashtags_map: Dict[int, List[str]]
    comment_counts_map: Dict[int, int]
    like_counts_map: Dict[int, int]
    liked_post_ids: Set[int]
    followed_user_ids: Set[UUID]


class PostReadService:
    def __init__(self):
        # 차단 유저 인메모리 캐시 (Key: current_user_id, Value: (timestamp, {blocked_user_ids}))
        self._block_cache: Dict[UUID, Tuple[float, Set[UUID]]] = {}
        self._cache_ttl = 60  # 캐시 유지 시간 (60초)

    def _get_cached_blocked_user_ids(self, db: Session, user_id: Optional[UUID]) -> Set[UUID]:
        if not user_id:
            return set()

        now = time.time()

        # 메모리 누수 방지: 캐시된 유저가 10,000명을 넘어가면 캐시 초기화
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

    def _get_mentions_for_posts(self, db: Session, post_ids: List[int]) -> Dict[int, List[Mention]]:
        if not post_ids:
            return {}

        mentions_query = db.query(PostMention.post_id, User.id, User.nickname, User.tag)\
            .join(User, User.id == PostMention.user_id)\
            .filter(PostMention.post_id.in_(post_ids), User.status == "ACTIVE").all()

        mentions_map: Dict[int, List[Mention]] = {pid: [] for pid in post_ids}
        for m in mentions_query:
            mentions_map[m.post_id].append(Mention(id=m.id, nickname=m.nickname, tag=m.tag))
        return mentions_map

    def _get_hashtags_for_posts(self, db: Session, post_ids: List[int]) -> Dict[int, List[str]]:
        if not post_ids:
            return {}

        hashtags_query = db.query(PostHashtag.post_id, Hashtag.normalized_keyword)\
            .join(Hashtag, Hashtag.id == PostHashtag.hashtag_id)\
            .filter(PostHashtag.post_id.in_(post_ids)).all()

        hashtags_map: Dict[int, List[str]] = {pid: [] for pid in post_ids}
        for h in hashtags_query:
            hashtags_map[h.post_id].append(h.normalized_keyword)
        return hashtags_map

    def _get_comment_counts_for_posts(self, db: Session, post_ids: List[int]) -> Dict[int, int]:
        if not post_ids:
            return {}

        counts = db.query(Comment.post_id, func.count(Comment.id))\
            .filter(Comment.post_id.in_(post_ids), Comment.status == "ACTIVE")\
            .group_by(Comment.post_id).all()

        return {pid: count for pid, count in counts}

    def _build_post_infos(
        self,
        db: Session,
        posts: List[Post],
        current_user_id: Optional[UUID],
        *,
        force_liked: bool = False,
    ) -> PostListContext:
        post_ids = [post.id for post in posts]
        if not post_ids:
            return PostListContext({}, {}, {}, {}, set(), set())

        cached_infos = post_cache_service.get_post_infos(post_ids)
        cache_miss_ids = [post_id for post_id in post_ids if cached_infos.get(post_id) is None]

        mentions_map: Dict[int, List[Mention]] = {post_id: [] for post_id in post_ids}
        hashtags_map: Dict[int, List[str]] = {post_id: [] for post_id in post_ids}
        comment_counts_map: Dict[int, int] = {}

        for post_id in post_ids:
            cached = cached_infos.get(post_id)
            if cached is None:
                continue
            mentions_map[post_id] = cached.mentions
            hashtags_map[post_id] = cached.hashtags
            comment_counts_map[post_id] = cached.comment_count

        if cache_miss_ids:
            db_mentions_map = self._get_mentions_for_posts(db, cache_miss_ids)
            db_hashtags_map = self._get_hashtags_for_posts(db, cache_miss_ids)
            db_comment_counts_map = self._get_comment_counts_for_posts(db, cache_miss_ids)

            to_cache: Dict[int, CachedPostInfo] = {}
            for post_id in cache_miss_ids:
                mentions = db_mentions_map.get(post_id, [])
                hashtags = db_hashtags_map.get(post_id, [])
                comment_count = db_comment_counts_map.get(post_id, 0)
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

        liked_post_ids: Set[int] = set()
        followed_user_ids: Set[UUID] = set()

        if current_user_id:
            if not force_liked:
                liked_logs = db.query(LikeLog.target_id).filter(
                    LikeLog.user_id == current_user_id,
                    LikeLog.target_type == "POST",
                    LikeLog.target_id.in_(post_ids),
                    LikeLog.is_active == 1,
                ).all()
                liked_post_ids = {log[0] for log in liked_logs}

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
            followed_user_ids=followed_user_ids,
        )

    def _build_post_list(
        self,
        posts_with_author: List[Tuple[Post, User]],
        *,
        context: PostListContext,
        limit: int,
        force_liked: bool = False,
    ) -> PostListResponse:
        result: List[PostResponse] = []
        for post, author in posts_with_author:
            result.append(
                PostMapper.to_post_response(
                    post,
                    author,
                    hashtags=context.hashtags_map.get(post.id, []),
                    mentions=context.mentions_map.get(post.id, []),
                    comment_count=context.comment_counts_map.get(post.id, 0),
                    like_count=context.like_counts_map.get(post.id, post.like_count or 0),
                    is_liked=force_liked or post.id in context.liked_post_ids,
                    is_following=post.user_id in context.followed_user_ids,
                )
            )

        next_cursor = result[-1].id if result else None
        return PostListResponse(items=result, next_cursor=next_cursor, has_next=len(result) == limit)

    def get_posts(self, db: Session, current_user_id: Optional[UUID], cursor: Optional[int], limit: int) -> PostListResponse:
        """게시물 피드 조회 로직"""
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        query = db.query(Post, User).join(User, Post.user_id == User.id).filter(
            Post.status == "ACTIVE",
            User.status == "ACTIVE"
        ).options(selectinload(Post.movies).selectinload(Movie.titles))

        if blocked_user_ids:
            query = query.filter(Post.user_id.notin_(blocked_user_ids))

        if cursor:
            query = query.filter(Post.id < cursor)

        posts_with_author = query.order_by(Post.id.desc()).limit(limit).all()
        posts = [post for post, _ in posts_with_author]
        context = self._build_post_infos(db, posts, current_user_id)

        return self._build_post_list(
            posts_with_author,
            context=context,
            limit=limit,
        )

    def get_my_liked_posts(self, db: Session, current_user_id: UUID, cursor: Optional[int], limit: int) -> PostListResponse:
        """내가 좋아요 누른 게시물 조회 로직"""
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        liked_post_ids_subquery = select(LikeLog.target_id).where(
            LikeLog.user_id == current_user_id,
            LikeLog.target_type == "POST",
            LikeLog.is_active == 1
        )

        query = db.query(Post, User).join(User, Post.user_id == User.id).filter(
            Post.id.in_(liked_post_ids_subquery),
            Post.status == "ACTIVE",
            User.status == "ACTIVE"
        ).options(selectinload(Post.movies).selectinload(Movie.titles))

        if blocked_user_ids:
            query = query.filter(Post.user_id.notin_(blocked_user_ids))

        if cursor:
            query = query.filter(Post.id < cursor)

        posts_with_author = query.order_by(Post.id.desc()).limit(limit).all()
        posts = [post for post, _ in posts_with_author]
        context = self._build_post_infos(db, posts, current_user_id, force_liked=True)

        return self._build_post_list(
            posts_with_author,
            context=context,
            limit=limit,
            force_liked=True,
        )

    def get_user_posts(
        self,
        db: Session,
        target_user_id: UUID,
        current_user_id: Optional[UUID],
        cursor: Optional[int],
        limit: int,
    ) -> PostListResponse:
        """특정 유저가 작성한 게시물 조회 로직"""
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)
        if target_user_id in blocked_user_ids:
            return PostListResponse(items=[], next_cursor=None, has_next=False)

        query = db.query(Post, User).join(User, Post.user_id == User.id).filter(
            Post.user_id == target_user_id,
            Post.status == "ACTIVE",
            User.status == "ACTIVE"
        ).options(selectinload(Post.movies).selectinload(Movie.titles))

        if cursor:
            query = query.filter(Post.id < cursor)

        posts_with_author = query.order_by(Post.id.desc()).limit(limit).all()
        posts = [post for post, _ in posts_with_author]
        context = self._build_post_infos(db, posts, current_user_id)

        return self._build_post_list(
            posts_with_author,
            context=context,
            limit=limit,
        )

    def get_post_detail(self, db: Session, post_id: int, current_user_id: Optional[UUID]) -> PostResponse:
        """게시물 상세 조회 로직"""
        db_result = db.query(Post, User).join(User, Post.user_id == User.id)\
            .options(selectinload(Post.movies).selectinload(Movie.titles))\
            .filter(Post.id == post_id, Post.status == "ACTIVE").first()

        if not db_result:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."})

        post, author = db_result
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)
        if post.user_id in blocked_user_ids:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_BLOCKED_POST", "message": "차단된 사용자의 게시물입니다."})

        context = self._build_post_infos(db, [post], current_user_id)
        is_following = (
            post.user_id in context.followed_user_ids
            if current_user_id and author and author.status != "DELETED"
            else False
        )

        return PostMapper.to_post_response(
            post,
            author,
            hashtags=context.hashtags_map.get(post.id, []),
            mentions=context.mentions_map.get(post.id, []),
            comment_count=context.comment_counts_map.get(post.id, 0),
            like_count=context.like_counts_map.get(post.id, post.like_count or 0),
            is_liked=post.id in context.liked_post_ids,
            is_following=is_following,
        )

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

        query = db.query(Post, User).join(User, Post.user_id == User.id).filter(
            Post.id.in_(unique_ids),
            Post.status == "ACTIVE",
            User.status == "ACTIVE",
        ).options(selectinload(Post.movies).selectinload(Movie.titles))

        if blocked_user_ids:
            query = query.filter(Post.user_id.notin_(blocked_user_ids))

        posts_with_author = query.all()
        posts_by_id = {post.id: (post, author) for post, author in posts_with_author}
        posts = [posts_by_id[pid][0] for pid in unique_ids if pid in posts_by_id]
        context = self._build_post_infos(db, posts, current_user_id)

        result: list[PostResponse] = []
        for post_id in post_ids:
            if post_id not in posts_by_id:
                continue
            post, author = posts_by_id[post_id]
            result.append(
                PostMapper.to_post_response(
                    post,
                    author,
                    hashtags=context.hashtags_map.get(post.id, []),
                    mentions=context.mentions_map.get(post.id, []),
                    comment_count=context.comment_counts_map.get(post.id, 0),
                    like_count=context.like_counts_map.get(post.id, post.like_count or 0),
                    is_liked=post.id in context.liked_post_ids,
                    is_following=post.user_id in context.followed_user_ids,
                )
            )
        return result


post_read_service = PostReadService()
