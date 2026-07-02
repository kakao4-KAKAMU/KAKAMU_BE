from datetime import date, datetime, timedelta
from typing import List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Block, Comment, Follow, Hashtag, LikeLog, Post, PostHashtag, PostMention, User
from app.models.movie import Genre, Movie, MovieStaff, People
from app.models.search_log import SearchDailyStat
from app.models.user import User as UserModel
from app.schemas.response.search import (
    GenreListResponse,
    PersonFilterSearchResponse,
    PostSearchResponse,
    SearchPost,
    TrendItem,
    TrendSearchResponse,
    UserSearchResponse,
)
from app.schemas.mapper.genre import GenreMapper
from app.schemas.mapper.mention import MentionMapper
from app.schemas.mapper.movie import MovieMapper
from app.schemas.mapper.pagination import PaginationMapper
from app.schemas.mapper.person import PersonMapper
from app.schemas.mapper.post import PostMapper
from app.schemas.mapper.user import UserMapper
from app.service.like.like_count_service import like_count_service
from app.service.post.query.select_post_new import PostInfoQueryOptions, PostReadServiceNew
from app.service.post.read_post import post_read_service
from app.service.save.save_lookup import get_saved_target_ids


class SearchService:
    genre_response: GenreListResponse = GenreListResponse(
        genres=[],
    )
    def get_genre_list(self, db: Session) -> GenreListResponse:
        if len(self.genre_response.genres) > 0:
            return self.genre_response
        genres = db.query(Genre).order_by(Genre.genre_name.asc()).all()
        self.genre_response = GenreListResponse(
            genres=[GenreMapper.to_genre(genre) for genre in genres],
        )
        return self.genre_response

    def search_people(
        self,
        db: Session,
        *,
        search_pattern: Optional[str] = None,
        jobs: Optional[List[str]] = None,
        sort: str = "name_asc",
        skip: int = 0,
        limit: int = 20,
    ) -> PersonFilterSearchResponse:
        query = db.query(People)
        if search_pattern:
            query = query.filter(
                or_(
                    People.person_name.ilike(search_pattern),
                    People.person_name_eng.ilike(search_pattern),
                )
            )
        if jobs:
            query = query.join(MovieStaff, People.id == MovieStaff.people_id).filter(MovieStaff.job.in_(jobs))

        if sort == "name_desc":
            query = query.order_by(People.person_name.desc(), People.id.desc())
        else:
            query = query.order_by(People.person_name.asc(), People.id.desc())

        total_count = query.count()
        people = query.offset(skip).limit(limit).all()
        return PersonFilterSearchResponse(
            items=[PersonMapper.to_person(person) for person in people],
            skip=skip,
            limit=limit,
            total_count=total_count,
        )

    def search_users(
        self,
        db: Session,
        search_pattern: str,
        *,
        cursor: Optional[str] = None,
        limit: int = 20,
        current_user_id: Optional[UUID] = None,
    ) -> UserSearchResponse:
        query = db.query(UserModel).filter(
            UserModel.status == "ACTIVE",
            or_(
                UserModel.username.ilike(search_pattern),
                UserModel.nickname.ilike(search_pattern),
                func.concat(UserModel.nickname, "#", UserModel.tag).ilike(search_pattern),
            ),
        )

        if current_user_id:
            blocked_by_me = select(Block.blocked_id).where(Block.blocker_id == current_user_id)
            blocking_me = select(Block.blocker_id).where(Block.blocked_id == current_user_id)
            query = query.filter(UserModel.id.notin_(blocked_by_me), UserModel.id.notin_(blocking_me))

        if cursor:
            try:
                last_nickname, last_id_str = cursor.rsplit(",", 1)
                last_id = UUID(last_id_str)
                query = query.filter(
                    or_(
                        UserModel.nickname > last_nickname,
                        (UserModel.nickname == last_nickname) & (UserModel.id < last_id),
                    )
                )
            except (ValueError, TypeError):
                pass

        query = query.order_by(UserModel.nickname.asc(), UserModel.id.desc())
        results = query.limit(limit).all()

        followed_user_ids: Set[UUID] = set()
        if current_user_id and results:
            target_user_ids = [user.id for user in results]
            follows = db.query(Follow.following_id).filter(
                Follow.follower_id == current_user_id,
                Follow.following_id.in_(target_user_ids),
            ).all()
            followed_user_ids = {follow[0] for follow in follows}

        next_cursor = None
        if len(results) == limit:
            last_item = results[-1]
            next_cursor = f"{last_item.nickname},{last_item.id}"

        return UserSearchResponse(
            items=[
                UserMapper.to_simple_with_follow(
                    user,
                    is_following=user.id in followed_user_ids,
                )
                for user in results
            ],
            meta=PaginationMapper.build_cursor_meta(
                next_cursor=next_cursor,
                has_next=next_cursor is not None,
            ),
        )

    def search_posts(
        self,
        db: Session,
        search_pattern: str,
        *,
        cursor: Optional[int] = None,
        limit: int = 20,
        current_user_id: Optional[UUID] = None,
        order_by_likes: bool = False,
        fallback: bool = False,
        message: Optional[str] = None,
    ) -> PostSearchResponse:
        blocked_user_ids = post_read_service._get_cached_blocked_user_ids(db, current_user_id)

        filters: list = [
            User.status == "ACTIVE",
            or_(Post.title.ilike(search_pattern), Post.content.ilike(search_pattern)),
        ]
        if blocked_user_ids:
            filters.append(Post.user_id.notin_(blocked_user_ids))
        if cursor is not None:
            filters.append(Post.id < cursor)

        order_by = (
            (Post.like_count.desc(), Post.id.desc())
            if order_by_likes
            else Post.id.desc()
        )

        _, ordered_post_ids = PostReadServiceNew.get_post_info_by_ids(
            db,
            None,
            options=PostInfoQueryOptions(
                filters=tuple(filters),
                order_by=order_by,
                limit=limit,
            ),
        )
        if not ordered_post_ids:
            return PostSearchResponse(
                items=[],
                meta=PaginationMapper.build_cursor_meta(),
                fallback=fallback or None,
                message=message,
            )

        info_map, ordered_post_ids = PostReadServiceNew.build_post_infos(
            db, ordered_post_ids, current_user_id
        )
        items = PostMapper.to_search_posts(info_map, ordered_post_ids)
        next_cursor = ordered_post_ids[-1] if len(ordered_post_ids) == limit else None

        return PostSearchResponse(
            items=items,
            meta=PaginationMapper.build_cursor_meta(
                next_cursor=next_cursor,
                has_next=next_cursor is not None,
            ),
            fallback=fallback or None,
            message=message,
        )

    def get_trend_keywords(self, db: Session, limit: int = 10) -> TrendSearchResponse:
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        trends = (
            db.query(SearchDailyStat)
            .filter(SearchDailyStat.stat_date == yesterday)
            .order_by(SearchDailyStat.search_count.desc(), SearchDailyStat.id.asc())
            .limit(limit)
            .all()
        )
        return TrendSearchResponse(
            stat_date=yesterday,
            items=[
                TrendItem(
                    rank=idx + 1,
                    keyword=trend.keyword,
                    search_count=trend.search_count,
                )
                for idx, trend in enumerate(trends)
            ],
        )

    def _map_posts(
        self,
        db: Session,
        posts_with_author: List[Tuple[Post, UserModel]],
        current_user_id: Optional[UUID],
    ) -> List[SearchPost]:
        post_ids = [post.id for post, _ in posts_with_author]
        author_user_ids = list({post.user_id for post, _ in posts_with_author})

        hashtags_map = self._get_hashtags_for_posts(db, post_ids)
        mentions_map = self._get_mentions_for_posts(db, post_ids)
        comment_counts_map = self._get_comment_counts_for_posts(db, post_ids)
        like_counts_map = like_count_service.resolve_like_counts(
            "POST",
            {post.id: post.like_count or 0 for post, _ in posts_with_author},
        )

        liked_post_ids: Set[int] = set()
        saved_post_ids: Set[int] = set()
        followed_user_ids: Set[UUID] = set()
        if current_user_id:
            liked_logs = db.query(LikeLog.target_id).filter(
                LikeLog.user_id == current_user_id,
                LikeLog.target_type == "POST",
                LikeLog.target_id.in_(post_ids),
                LikeLog.is_active == 1,
            ).all()
            liked_post_ids = {log[0] for log in liked_logs}
            saved_post_ids = get_saved_target_ids(
                db, current_user_id, "POST", post_ids
            )

            follows = db.query(Follow.following_id).filter(
                Follow.follower_id == current_user_id,
                Follow.following_id.in_(author_user_ids),
            ).all()
            followed_user_ids = {follow[0] for follow in follows}

        return [
            PostMapper.to_search_post(
                post,
                author,
                hashtags=hashtags_map.get(post.id, []),
                mentions=mentions_map.get(post.id, []),
                movies=[MovieMapper.to_movie(movie) for movie in post.movies],
                comment_count=comment_counts_map.get(post.id, 0),
                like_count=like_counts_map.get(post.id, post.like_count or 0),
                is_liked=post.id in liked_post_ids,
                is_saved=post.id in saved_post_ids,
                is_following=post.user_id in followed_user_ids,
            )
            for post, author in posts_with_author
        ]

    @staticmethod
    def _get_hashtags_for_posts(db: Session, post_ids: List[int]) -> dict:
        if not post_ids:
            return {}

        rows = (
            db.query(PostHashtag.post_id, Hashtag.normalized_keyword)
            .join(Hashtag, Hashtag.id == PostHashtag.hashtag_id)
            .filter(PostHashtag.post_id.in_(post_ids))
            .all()
        )
        result = {post_id: [] for post_id in post_ids}
        for post_id, keyword in rows:
            result[post_id].append(keyword)
        return result

    @staticmethod
    def _get_mentions_for_posts(db: Session, post_ids: List[int]) -> dict:
        if not post_ids:
            return {}

        rows = (
            db.query(PostMention.post_id, UserModel.id, UserModel.nickname, UserModel.tag)
            .join(UserModel, UserModel.id == PostMention.user_id)
            .filter(PostMention.post_id.in_(post_ids), UserModel.status == "ACTIVE")
            .all()
        )
        result = {post_id: [] for post_id in post_ids}
        for post_id, user_id, nickname, tag in rows:
            result[post_id].append(MentionMapper.from_row(user_id, nickname, tag))
        return result

    @staticmethod
    def _get_comment_counts_for_posts(db: Session, post_ids: List[int]) -> dict:
        if not post_ids:
            return {}

        rows = (
            db.query(Comment.post_id, func.count(Comment.id))
            .filter(Comment.post_id.in_(post_ids), Comment.status == "ACTIVE")
            .group_by(Comment.post_id)
            .all()
        )
        return {post_id: count for post_id, count in rows}


search_service = SearchService()
