from typing import Any, Optional, Type

from sqlalchemy import exists, func, or_, select
from sqlalchemy.sql.elements import ColumnElement

from app.models.movie import Movie, MovieTitle
from app.models.post import Post, PostStatus
from app.models.user import User


def build_ilike_pattern(q: str) -> str:
    """검색어 패턴 생성 (양방향 부분 일치, pg_trgm GIN 인덱스 활용)."""
    return f"%{q}%"


def user_display_name(user_model: Type[User] = User) -> ColumnElement[Any]:
    """nickname#tag 표현식 SSOT (인덱스 표현식과 동일하게 || 사용)."""
    return user_model.nickname + "#" + user_model.tag


def build_user_trgm_filter(
    pattern: str,
    user_model: Type[User] = User,
) -> ColumnElement[bool]:
    """nickname 또는 nickname#tag 부분 일치 필터."""
    return or_(
        user_model.nickname.ilike(pattern),
        user_display_name(user_model).ilike(pattern),
    )


def build_post_trgm_filter(
    pattern: str,
    post_model: Type[Post] = Post,
) -> ColumnElement[bool]:
    """post title/content 부분 일치 필터."""
    return or_(
        post_model.title.ilike(pattern),
        post_model.content.ilike(pattern),
    )


def post_trgm_match_subquery(
    pattern: str,
    *,
    cursor: Optional[int] = None,
    limit: int,
    order_by_likes: bool = False,
    post_model: Type[Post] = Post,
) -> Any:
    """ILIKE 매칭 post를 trgm GIN 인덱스로 선별 (ix_post_title_content_trgm 활용).

    user 조인 전에 post를 먼저 스캔해 Nested Loop(user → post) 플랜을 방지한다.
    """
    stmt = select(post_model.id).where(
        post_model.status == PostStatus.ACTIVE,
        build_post_trgm_filter(pattern, post_model),
    )
    if cursor is not None:
        stmt = stmt.where(post_model.id < cursor)
    if order_by_likes:
        stmt = stmt.order_by(post_model.like_count.desc(), post_model.id.desc())
    else:
        stmt = stmt.order_by(post_model.id.desc())
    return stmt.limit(limit).subquery("post_trgm_matches")


def movie_title_exists(
    movie_model: Type[Movie],
    pattern: str,
    title_model: Type[MovieTitle] = MovieTitle,
) -> ColumnElement[bool]:
    """movie_title.title_name ILIKE 기반 EXISTS 서브쿼리 (ix_movie_title_trgm 활용)."""
    return exists(
        select(1).where(
            title_model.movie_id == movie_model.id,
            title_model.title_name.ilike(pattern),
        )
    )


def movie_title_search_scores_subquery(
    search_query: str,
    pattern: str,
    title_model: Type[MovieTitle] = MovieTitle,
) -> Any:
    """ILIKE 매칭 title을 trgm 인덱스로 한 번 스캔해 movie_id별 최대 similarity.

    EXISTS + correlated MAX(similarity) 서브쿼리 대신 사용한다.
    후자는 movie_title_pkey Index Only Scan 후 ILIKE 재필터링이 발생한다.
    """
    return (
        select(
            title_model.movie_id.label("movie_id"),
            func.max(func.similarity(title_model.title_name, search_query)).label("score"),
        )
        .where(title_model.title_name.ilike(pattern))
        .group_by(title_model.movie_id)
        .subquery("movie_title_scores")
    )
