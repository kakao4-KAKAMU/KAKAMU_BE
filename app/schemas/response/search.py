from datetime import date
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from app.schemas.base.genre import Genre
from app.schemas.base.mention import Mention
from app.schemas.base.movie import Movie
from app.schemas.base.pagination import CursorPaginationMeta
from app.schemas.base.person import Person
from app.schemas.base.post import PostItem
from app.schemas.base.trend import TrendItem
from app.schemas.base.user import UserSimpleWithFollow

T = TypeVar("T")

PaginationMeta = CursorPaginationMeta
MentionUserItem = Mention

__all__ = [
    "SearchBaseResponse",
    "Genre",
    "Movie",
    "Person",
    "UserSimple",
    "MentionUserItem",
    "SearchPost",
    "PaginationMeta",
    "CursorSearchResponse",
    "OffsetSearchResponse",
    "GenreListResponse",
    "MovieTabSearchResponse",
    "MovieFilterSearchResponse",
    "PersonFilterSearchResponse",
    "UserSearchResponse",
    "PostSearchResponse",
    "TrendItem",
    "TrendSearchResponse",
]


class SearchBaseResponse(BaseModel):
    status: str = Field(default="success")


class SearchPost(PostItem):
    pass


class CursorSearchResponse(SearchBaseResponse, Generic[T]):
    items: List[T]
    meta: PaginationMeta


class OffsetSearchResponse(SearchBaseResponse, Generic[T]):
    items: List[T]
    skip: int
    limit: int
    total_count: int


class GenreListResponse(SearchBaseResponse):
    genres: List[Genre]


class MovieTabSearchResponse(CursorSearchResponse[Movie]):
    items: List[Movie]


class MovieFilterSearchResponse(OffsetSearchResponse[Movie]):
    items: List[Movie]


class PersonFilterSearchResponse(OffsetSearchResponse[Person]):
    items: List[Person]


class UserSearchResponse(CursorSearchResponse[UserSimpleWithFollow]):
    items: List[UserSimpleWithFollow]


class PostSearchResponse(CursorSearchResponse[SearchPost]):
    items: List[SearchPost]
    fallback: Optional[bool] = None
    message: Optional[str] = None


class TrendSearchResponse(SearchBaseResponse):
    stat_date: date
    items: List[TrendItem]
