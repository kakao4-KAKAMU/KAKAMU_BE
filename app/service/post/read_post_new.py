import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import (
    Comment,
    Hashtag,
    LikeLog,
    Movie,
    Post,
    PostHashtag,
    PostMention,
    PostMovie,
    SaveLog,
    User,
    PostStatus,
    UserStatus,
    CommentStatus,
)
from app.models.movie import MovieTitle

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
    def _build_relation_subqueries(post_ids: List[int] | None):
        hashtags_subq = (
            select(
                PostHashtag.post_id,
                func.json_agg(Hashtag.normalized_keyword).label("hashtags"),
            )
            .join(Hashtag, Hashtag.id == PostHashtag.hashtag_id)
            .group_by(PostHashtag.post_id)
        )
        if post_ids:
            hashtags_subq = hashtags_subq.where(PostHashtag.post_id.in_(post_ids))
        hashtags_subq = hashtags_subq.subquery()

        mentions_subq = (
            select(
                PostMention.post_id,
                func.json_agg(
                    func.json_build_object(
                        "id",
                        User.id,
                        "nickname",
                        User.nickname,
                        "tag",
                        User.tag,
                    )
                ).label("mentions"),
            )
            .join(User, User.id == PostMention.user_id)
            .where(User.status == UserStatus.ACTIVE)
            .group_by(PostMention.post_id)
        )
        if post_ids:
            mentions_subq = mentions_subq.where(PostMention.post_id.in_(post_ids))
        mentions_subq = mentions_subq.subquery()

        title_subq = (
            select(MovieTitle.title_name)
            .where(MovieTitle.movie_id == Movie.id)
            .order_by(MovieTitle.is_original.desc())
            .limit(1)
            .correlate(Movie)
            .scalar_subquery()
        )

        movies_subq = (
            select(
                PostMovie.post_id,
                func.json_agg(
                    func.json_build_object(
                        "id",
                        Movie.id,
                        "poster_url",
                        Movie.poster_url,
                        "release_date",
                        Movie.release_date,
                        "title",
                        func.coalesce(title_subq, "제목 없음"),
                    )
                ).label("movies"),
            )
            .join(Movie, Movie.id == PostMovie.movie_id)
            .group_by(PostMovie.post_id)
        )
        if post_ids:
            movies_subq = movies_subq.where(PostMovie.post_id.in_(post_ids))
        movies_subq = movies_subq.subquery()

        return mentions_subq, hashtags_subq, movies_subq

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

        mentions_subq, hashtags_subq, movies_subq = PostReadServiceNew._build_relation_subqueries(
            post_ids
        )
        empty_json = text("'[]'::json")

        query = db.query(
            Post,
            User,
            func.coalesce(mentions_subq.c.mentions, empty_json).label("mentions"),
            func.coalesce(hashtags_subq.c.hashtags, empty_json).label("hashtags"),
            func.coalesce(movies_subq.c.movies, empty_json).label("movies"),
        )

        if opts.include_author:
            query = query.join(User, Post.user_id == User.id)
        else:
            query = query.outerjoin(User, Post.user_id == User.id)

        query = (
            query.outerjoin(mentions_subq, mentions_subq.c.post_id == Post.id)
            .outerjoin(hashtags_subq, hashtags_subq.c.post_id == Post.id)
            .outerjoin(movies_subq, movies_subq.c.post_id == Post.id)
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

            info_map[post.id] = {
                "post": post,
                "author": author,
                "mentions": PostReadServiceNew._parse_json_col(mentions_raw),
                "hashtags": PostReadServiceNew._parse_json_col(hashtags_raw),
                "movies": PostReadServiceNew._parse_json_col(movies_raw),
            }
            ordered_post_ids.append(post.id)

        return info_map, ordered_post_ids

    @staticmethod
    def get_post_counts_by_ids(db: Session, post_ids: List[int]) -> Dict[int, dict]:
        if not post_ids:
            return {}

        comment_subq = (
            select(Comment.post_id, func.count(Comment.id).label("comment_count"))
            .where(Comment.status == CommentStatus.ACTIVE)
            .filter(Comment.post_id.in_(post_ids))
            .group_by(Comment.post_id)
            .subquery()
        )
        post_counts_query = (
            db.query(Post.id, Post.like_count, comment_subq.c.comment_count)
            .outerjoin(comment_subq, comment_subq.c.post_id == Post.id)
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

        like_subq = (
            select(LikeLog.target_id, func.count(LikeLog.id).label("is_liked"))
            .where(LikeLog.target_type == "POST", LikeLog.is_active == 1)
            .filter(LikeLog.target_id.in_(post_ids), LikeLog.user_id == current_user_id)
            .group_by(LikeLog.target_id)
            .subquery()
        )
        save_subq = (
            select(SaveLog.target_id, func.count(SaveLog.id).label("is_saved"))
            .where(SaveLog.target_type == "POST", SaveLog.is_active == 1)
            .filter(SaveLog.target_id.in_(post_ids), SaveLog.user_id == current_user_id)
            .group_by(SaveLog.target_id)
            .subquery()
        )

        post_status_query = (
            db.query(Post.id, like_subq.c.is_liked, save_subq.c.is_saved)
            .outerjoin(like_subq, like_subq.c.target_id == Post.id)
            .outerjoin(save_subq, save_subq.c.target_id == Post.id)
            .filter(Post.id.in_(post_ids))
            .all()
        )
        return {
            post_status.id: {
                "is_liked": bool(post_status.is_liked),
                "is_saved": bool(post_status.is_saved),
            }
            for post_status in post_status_query
        }

    @staticmethod
    def build_post_infos(
        db: Session, post_id_list: List[int], current_user_id: Optional[UUID]
    ) -> List[dict]:
        if not post_id_list:
            return []

        post_info_map, _ = PostReadServiceNew.get_post_info_by_ids(db, post_id_list)
        post_counts_map = PostReadServiceNew.get_post_counts_by_ids(db, post_id_list)
        post_status_map = PostReadServiceNew.get_post_status_by_user_and_post_ids(
            db, current_user_id, post_id_list
        )
        return [
            post_info_map.get(post_id, {})
            | post_counts_map.get(post_id, {})
            | post_status_map.get(post_id, {"is_liked": False, "is_saved": False})
            for post_id in post_id_list
        ]
