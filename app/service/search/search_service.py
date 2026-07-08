from datetime import date, datetime, timedelta
from typing import List, Optional, Set
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Block, Follow
from app.models.movie import Genre, MovieStaff, People
from app.models.search_log import SearchDailyStat
from app.models.user import User as UserModel, UserStatus
from app.schemas.response.search import (
    GenreListResponse,
    PersonFilterSearchResponse,
    PostSearchResponse,
    TrendItem,
    TrendSearchResponse,
    UserSearchResponse,
)
from app.schemas.mapper.genre import GenreMapper
from app.schemas.mapper.pagination import PaginationMapper
from app.schemas.mapper.person import PersonMapper
from app.schemas.mapper.post import PostMapper
from app.schemas.mapper.user import UserMapper
from app.service.post.read_post import post_read_service
from app.utils.trgm_search import build_user_trgm_filter


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
            UserModel.status == UserStatus.ACTIVE,
            build_user_trgm_filter(search_pattern, UserModel),
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
        posts_with_author, context = post_read_service.fetch_search_posts_with_context(
            db,
            search_pattern=search_pattern,
            cursor=cursor,
            limit=limit,
            order_by_likes=order_by_likes,
            current_user_id=current_user_id,
        )

        if not posts_with_author:
            return PostSearchResponse(
                items=[],
                meta=PaginationMapper.build_cursor_meta(),
                fallback=fallback or None,
                message=message,
            )

        items = PostMapper.to_search_posts(posts_with_author, context=context)
        next_cursor = posts_with_author[-1][0].id if len(posts_with_author) == limit else None

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


search_service = SearchService()
