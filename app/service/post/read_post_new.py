import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.schemas.base.mention import Mention
from pydantic import TypeAdapter
from app.models import (
    LikeLog,
    Post,
    PostCommentCount,
    PostHashtagAgg,
    PostMentionAgg,
    PostMovieAgg,
    SaveLog,
    User,
    PostStatus,
)
from app.schemas.base.movie import Movie as MovieBase

@dataclass
class PostInfoQueryOptions:
    filters: tuple = ()
    joins: tuple = ()
    loader_options: tuple = ()
    order_by: Any | None = None
    limit: int | None = None
    include_author: bool = True


class PostReadServiceNew:

    @staticmethod
    def _parse_json_col(value):
        if isinstance(value, str):
            return json.loads(value)
        return value or []

    @staticmethod
    def _parse_mentions(value):
        return TypeAdapter(List[Mention]).validate_python(value)

    @staticmethod
    def _parse_hashtags(value):
        return TypeAdapter(List[str]).validate_python(value)

    @staticmethod
    def _parse_movies(value):
        return TypeAdapter(List[MovieBase]).validate_python(value)

    @staticmethod
    def fetch_feed_posts(
        db: Session,
        *,
        options: PostInfoQueryOptions | None = None,
    ) -> Tuple[List[Tuple[Post, User]], List[int]]:
        """피드 선별용 경량 쿼리: post + user만 조회 (aggregate view join 없음)."""
        opts = options or PostInfoQueryOptions()

        query = db.query(Post, User).join(User, Post.user_id == User.id).filter(
            Post.status == PostStatus.ACTIVE
        )

        for join_clause in opts.joins:
            query = query.join(*join_clause) if isinstance(join_clause, tuple) else query.join(join_clause)

        for filter_clause in opts.filters:
            query = query.filter(filter_clause)

        if opts.loader_options:
            query = query.options(*opts.loader_options)

        if opts.order_by is not None:
            query = query.order_by(opts.order_by)

        if opts.limit is not None:
            query = query.limit(opts.limit)

        query_result = query.all()
        ordered_post_ids = [post.id for post, _ in query_result]
        return query_result, ordered_post_ids

    @staticmethod
    def get_post_agg_by_ids(
        db: Session,
        post_ids: List[int],
    ) -> Dict[int, dict]:
        """aggregate 테이블에서 mentions/hashtags/movies만 조회."""
        if not post_ids:
            return {}

        empty_json = text("'[]'::jsonb")
        query_result = (
            db.query(
                Post.id,
                func.coalesce(PostMentionAgg.mentions, empty_json).label("mentions"),
                func.coalesce(PostHashtagAgg.hashtags, empty_json).label("hashtags"),
                func.coalesce(PostMovieAgg.movies, empty_json).label("movies"),
            )
            .outerjoin(PostMentionAgg, PostMentionAgg.post_id == Post.id)
            .outerjoin(PostHashtagAgg, PostHashtagAgg.post_id == Post.id)
            .outerjoin(PostMovieAgg, PostMovieAgg.post_id == Post.id)
            .filter(Post.id.in_(post_ids))
            .all()
        )

        agg_map: Dict[int, dict] = {}
        for post_id, mentions_raw, hashtags_raw, movies_raw in query_result:
            agg_map[post_id] = {
                "mentions": PostReadServiceNew._parse_mentions(
                    PostReadServiceNew._parse_json_col(mentions_raw)
                ),
                "hashtags": PostReadServiceNew._parse_hashtags(
                    PostReadServiceNew._parse_json_col(hashtags_raw)
                ),
                "movies": PostReadServiceNew._parse_movies(
                    PostReadServiceNew._parse_json_col(movies_raw)
                ),
            }
        return agg_map

    @staticmethod
    def get_post_info_by_ids(
        db: Session,
        post_ids: List[int] | None = None,
        *,
        options: PostInfoQueryOptions | None = None,
    ) -> Tuple[Dict[int, dict], List[int]]:
        opts = options or PostInfoQueryOptions()
        if post_ids is not None and not post_ids:
            return {}, []

        empty_json = text("'[]'::json")

        query = db.query(
            Post,
            User,
            func.coalesce(PostMentionAgg.mentions, empty_json).label("mentions"),
            func.coalesce(PostHashtagAgg.hashtags, empty_json).label("hashtags"),
            func.coalesce(PostMovieAgg.movies, empty_json).label("movies"),
        )

        if opts.include_author:
            query = query.join(User, Post.user_id == User.id)
        else:
            query = query.outerjoin(User, Post.user_id == User.id)

        query = (
            query.outerjoin(PostMentionAgg, PostMentionAgg.post_id == Post.id)
            .outerjoin(PostHashtagAgg, PostHashtagAgg.post_id == Post.id)
            .outerjoin(PostMovieAgg, PostMovieAgg.post_id == Post.id)
            .filter(Post.status == PostStatus.ACTIVE)
        )

        if post_ids is not None:
            query = query.filter(Post.id.in_(post_ids))

        for join_clause in opts.joins:
            query = query.join(*join_clause) if isinstance(join_clause, tuple) else query.join(join_clause)

        for filter_clause in opts.filters:
            query = query.filter(filter_clause)

        if opts.loader_options:
            query = query.options(*opts.loader_options)

        if opts.order_by is not None:
            query = query.order_by(opts.order_by)

        if opts.limit is not None:
            query = query.limit(opts.limit)

        query_result = query.all()

        info_map: Dict[int, dict] = {}
        ordered_post_ids: List[int] = []

        for row in query_result:
            post, author, mentions_raw, hashtags_raw, movies_raw = row

            mentions = PostReadServiceNew._parse_mentions(PostReadServiceNew._parse_json_col(mentions_raw))
            hashtags = PostReadServiceNew._parse_hashtags(PostReadServiceNew._parse_json_col(hashtags_raw))
            movies = PostReadServiceNew._parse_movies(PostReadServiceNew._parse_json_col(movies_raw))
            info_map[post.id] = {
                "post": post,
                "author": author,
                "mentions": mentions,
                "hashtags": hashtags,
                "movies": movies,
            }
            ordered_post_ids.append(post.id)

        return info_map, ordered_post_ids

    @staticmethod
    def get_post_counts_by_ids(db: Session, post_ids: List[int]) -> Dict[int, dict]:
        if not post_ids:
            return {}

        post_counts_query = (
            db.query(Post.id, Post.like_count, PostCommentCount.comment_count)
            .outerjoin(PostCommentCount, PostCommentCount.post_id == Post.id)
            .filter(Post.id.in_(post_ids))
            .all()
        )
        return {
            post_count.id: {
                "like_count": post_count.like_count,
                "comment_count": post_count.comment_count or 0,
            }
            for post_count in post_counts_query
        }

    @staticmethod
    def get_post_status_by_user_and_post_ids(
        db: Session, current_user_id: Optional[UUID], post_ids: List[int]
    ) -> Dict[int, dict]:
        if not post_ids:
            return {}

        if not current_user_id:
            return {
                post_id: {
                    "is_liked": False,
                    "is_saved": False,
                }
                for post_id in post_ids
            }

        liked_rows = (
            db.query(LikeLog.target_id)
            .filter(
                LikeLog.user_id == current_user_id,
                LikeLog.target_type == "POST",
                LikeLog.is_active == 1,
                LikeLog.target_id.in_(post_ids),
            )
            .all()
        )
        saved_rows = (
            db.query(SaveLog.target_id)
            .filter(
                SaveLog.user_id == current_user_id,
                SaveLog.target_type == "POST",
                SaveLog.is_active == 1,
                SaveLog.target_id.in_(post_ids),
            )
            .all()
        )
        liked_ids = {row[0] for row in liked_rows}
        saved_ids = {row[0] for row in saved_rows}

        return {
            post_id: {
                "is_liked": post_id in liked_ids,
                "is_saved": post_id in saved_ids,
            }
            for post_id in post_ids
        }

    @staticmethod
    def build_post_infos(
        db: Session,
        post_id_list: List[int],
        current_user_id: Optional[UUID],
        options: PostInfoQueryOptions | None = None,
    ) -> List[dict]:
        if not post_id_list:
            return []

        post_info_map, ordered_post_ids = PostReadServiceNew.get_post_info_by_ids(db, post_id_list, options=options)
        post_counts_map = PostReadServiceNew.get_post_counts_by_ids(db, post_id_list)
        post_status_map = PostReadServiceNew.get_post_status_by_user_and_post_ids(
            db, current_user_id, post_id_list
        )
        return [
            post_info_map.get(post_id, {})
            | post_counts_map.get(post_id, {})
            | post_status_map.get(post_id, {"is_liked": False, "is_saved": False})
            for post_id in ordered_post_ids
        ]
