import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.schemas.base.mention import Mention
from app.service.post.schema.read_post_base import (
    GetPostInfoStruct,
    GetPostCountsStruct,
    GetPostStatusStruct,
    GetPostInfoFullStruct,
)
from pydantic import TypeAdapter
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
    Follow
)
from app.models.movie import MovieOriginalTitle
from app.schemas.base.movie import Movie as MovieBase
from app.service.redis.post_cache import CachedPostInfo, post_cache_service

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
    def _apply_order_by(query, order_by: Any):
        if isinstance(order_by, (tuple, list)):
            return query.order_by(*order_by)
        return query.order_by(order_by)

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
            .where(User.status == "ACTIVE")
            .group_by(PostMention.post_id)
        )
        if post_ids:
            mentions_subq = mentions_subq.where(PostMention.post_id.in_(post_ids))
        mentions_subq = mentions_subq.subquery()

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
                        MovieOriginalTitle.title_name,
                    )
                ).label("movies"),
            )
            .join(Movie, Movie.id == PostMovie.movie_id)
            .join(MovieOriginalTitle, MovieOriginalTitle.movie_id == Movie.id)
            .group_by(PostMovie.post_id)
        )
        if post_ids:
            movies_subq = movies_subq.where(PostMovie.post_id.in_(post_ids))
        movies_subq = movies_subq.subquery()

        return mentions_subq, hashtags_subq, movies_subq

    @staticmethod
    def _build_info_map_from_rows(
        rows: list,
    ) -> Tuple[Dict[int, GetPostInfoStruct], List[int], Dict[int, CachedPostInfo]]:
        info_map: Dict[int, GetPostInfoStruct] = {}
        ordered_post_ids: List[int] = []
        cache_payload: Dict[int, CachedPostInfo] = {}

        for row in rows:
            post, author, mentions_raw, hashtags_raw, movies_raw = row
            mentions = PostReadServiceNew._parse_mentions(
                PostReadServiceNew._parse_json_col(mentions_raw)
            )
            hashtags = PostReadServiceNew._parse_hashtags(
                PostReadServiceNew._parse_json_col(hashtags_raw)
            )
            movies = PostReadServiceNew._parse_movies(
                PostReadServiceNew._parse_json_col(movies_raw)
            )
            info_map[post.id] = GetPostInfoStruct(
                post=post,
                author=author,
                mentions=mentions,
                hashtags=hashtags,
                movies=movies,
            )
            ordered_post_ids.append(post.id)
            cache_payload[post.id] = CachedPostInfo(
                mentions=mentions,
                hashtags=hashtags,
                movies=movies,
            )

        return info_map, ordered_post_ids, cache_payload

    @staticmethod
    def _query_post_info_rows_from_db(
        db: Session,
        post_ids: List[int] | None,
        opts: PostInfoQueryOptions,
    ) -> list:
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
            .filter(Post.status == "ACTIVE")
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
            query = PostReadServiceNew._apply_order_by(query, opts.order_by)

        if opts.limit is not None:
            query = query.limit(opts.limit)

        return query.all()

    @staticmethod
    def _query_posts_and_authors_from_db(
        db: Session,
        post_ids: List[int],
        opts: PostInfoQueryOptions,
    ) -> list:
        query = db.query(Post, User)

        if opts.include_author:
            query = query.join(User, Post.user_id == User.id)
        else:
            query = query.outerjoin(User, Post.user_id == User.id)

        query = query.filter(Post.status == "ACTIVE", Post.id.in_(post_ids))

        for join_clause in opts.joins:
            query = query.join(*join_clause) if isinstance(join_clause, tuple) else query.join(join_clause)

        for filter_clause in opts.filters:
            query = query.filter(filter_clause)

        if opts.loader_options:
            query = query.options(*opts.loader_options)

        if opts.order_by is not None:
            query = PostReadServiceNew._apply_order_by(query, opts.order_by)

        if opts.limit is not None:
            query = query.limit(opts.limit)

        return query.all()

    @staticmethod
    def _merge_cached_infos(
        rows: list,
        cached_infos: Dict[int, CachedPostInfo],
    ) -> Tuple[Dict[int, GetPostInfoStruct], List[int]]:
        info_map: Dict[int, GetPostInfoStruct] = {}
        ordered_post_ids: List[int] = []

        for post, author in rows:
            cached = cached_infos[post.id]
            info_map[post.id] = GetPostInfoStruct(
                post=post,
                author=author,
                mentions=cached.mentions,
                hashtags=cached.hashtags,
                movies=cached.movies,
            )
            ordered_post_ids.append(post.id)

        return info_map, ordered_post_ids

    @staticmethod
    def get_post_info_by_ids(
        db: Session,
        post_ids: List[int] | None = None,
        *,
        options: PostInfoQueryOptions | None = None,
    ) -> Tuple[Dict[int, GetPostInfoStruct], List[int]]:
        opts = options or PostInfoQueryOptions()
        if post_ids is not None and not post_ids:
            return {}, []

        if post_ids is not None:
            cached_infos, miss_ids = post_cache_service.get_infos(post_ids)
            if not miss_ids:
                rows = PostReadServiceNew._query_posts_and_authors_from_db(db, post_ids, opts)
                return PostReadServiceNew._merge_cached_infos(rows, cached_infos)

            query_ids = miss_ids
            rows = PostReadServiceNew._query_post_info_rows_from_db(db, query_ids, opts)
            info_map, ordered_post_ids, cache_payload = PostReadServiceNew._build_info_map_from_rows(rows)
            post_cache_service.set_infos(cache_payload)

            if cached_infos:
                cached_rows = PostReadServiceNew._query_posts_and_authors_from_db(
                    db, list(cached_infos.keys()), opts
                )
                cached_map, _ = PostReadServiceNew._merge_cached_infos(cached_rows, cached_infos)
                info_map.update(cached_map)

            ordered_rows = PostReadServiceNew._query_posts_and_authors_from_db(
                db, list(info_map.keys()), opts
            )
            ordered_post_ids = [post.id for post, _ in ordered_rows]

            return info_map, ordered_post_ids

        rows = PostReadServiceNew._query_post_info_rows_from_db(db, post_ids, opts)
        info_map, ordered_post_ids, cache_payload = PostReadServiceNew._build_info_map_from_rows(rows)
        post_cache_service.set_infos(cache_payload)
        return info_map, ordered_post_ids

    @staticmethod
    def _query_post_counts_from_db(db: Session, post_ids: List[int]) -> Dict[int, GetPostCountsStruct]:
        comment_subq = (
            select(Comment.post_id, func.count(Comment.id).label("comment_count"))
            .where(Comment.status == "ACTIVE")
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
            post_count.id: GetPostCountsStruct(
                like_count=post_count.like_count,
                comment_count=post_count.comment_count or 0,
            )
            for post_count in post_counts_query
        }

    @staticmethod
    def get_post_counts_by_ids(db: Session, post_ids: List[int]) -> Dict[int, GetPostCountsStruct]:
        if not post_ids:
            return {}

        cached_counts, miss_ids = post_cache_service.get_counts(post_ids)
        if not miss_ids:
            return cached_counts

        db_counts = PostReadServiceNew._query_post_counts_from_db(db, miss_ids)
        post_cache_service.set_counts(db_counts)
        return {**cached_counts, **db_counts}

    @staticmethod
    def _query_post_status_from_db(
        db: Session, current_user_id: UUID, post_ids: List[int]
    ) -> Dict[int, GetPostStatusStruct]:
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

        following_subq = (
            select(Follow.following_id, func.count(Follow.following_id).label("is_following"))
            .where(Follow.follower_id == current_user_id)
            .group_by(Follow.following_id)
            .subquery()
        )

        post_status_query = (
            db.query(Post.id, like_subq.c.is_liked, save_subq.c.is_saved, following_subq.c.is_following)
            .outerjoin(like_subq, like_subq.c.target_id == Post.id)
            .outerjoin(following_subq, following_subq.c.following_id == Post.user_id)
            .outerjoin(save_subq, save_subq.c.target_id == Post.id)
            .filter(Post.id.in_(post_ids))
            .all()
        )
        return {
            post_status.id: GetPostStatusStruct(
                is_liked=bool(post_status.is_liked),
                is_saved=bool(post_status.is_saved),
                is_following=bool(post_status.is_following),
            )
            for post_status in post_status_query
        }

    @staticmethod
    def get_post_status_by_user_and_post_ids(
        db: Session, current_user_id: Optional[UUID], post_ids: List[int]
    ) -> Dict[int, GetPostStatusStruct]:
        if not post_ids:
            return {}

        if not current_user_id:
            return {
                post_id: GetPostStatusStruct(
                    is_liked=False,
                    is_saved=False,
                    is_following=False,
                )
                for post_id in post_ids
            }

        cached_statuses, miss_ids = post_cache_service.get_statuses(post_ids, current_user_id)
        if not miss_ids:
            return {
                post_id: GetPostStatusStruct(
                    is_liked=status.is_liked,
                    is_saved=status.is_saved,
                    is_following=status.is_following,
                )
                for post_id, status in cached_statuses.items()
            }

        db_statuses = PostReadServiceNew._query_post_status_from_db(db, current_user_id, miss_ids)
        post_cache_service.set_statuses(current_user_id, db_statuses)
        return {
            **{
                post_id: GetPostStatusStruct(
                    is_liked=status.is_liked,
                    is_saved=status.is_saved,
                    is_following=status.is_following,
                )
                for post_id, status in cached_statuses.items()
            },
            **db_statuses,
        }

    @staticmethod
    def build_post_infos(
        db: Session,
        post_id_list: List[int],
        current_user_id: Optional[UUID],
        options: PostInfoQueryOptions | None = None,
    ) -> Tuple[Dict[int, GetPostInfoFullStruct], List[int]]:
        if not post_id_list:
            return {}, []

        post_info_map, ordered_post_ids = PostReadServiceNew.get_post_info_by_ids(db, post_id_list, options=options)
        post_counts_map = PostReadServiceNew.get_post_counts_by_ids(db, post_id_list)
        post_status_map = PostReadServiceNew.get_post_status_by_user_and_post_ids(
            db, current_user_id, post_id_list
        )
        full_info_map: Dict[int, GetPostInfoFullStruct] = {}
        for post_id in ordered_post_ids:
            counts = post_counts_map.get(post_id, {})
            status = post_status_map.get(post_id, {})
            full_info_map[post_id] = GetPostInfoFullStruct(
                post=post_info_map[post_id]["post"],
                author=post_info_map[post_id]["author"],
                mentions=post_info_map[post_id]["mentions"],
                hashtags=post_info_map[post_id]["hashtags"],
                movies=post_info_map[post_id]["movies"],
                like_count=counts.get("like_count", 0) or 0,
                comment_count=counts.get("comment_count", 0) or 0,
                is_liked=status.get("is_liked", False),
                is_saved=status.get("is_saved", False),
                is_following=status.get("is_following", False),
            )
        return full_info_map, ordered_post_ids
