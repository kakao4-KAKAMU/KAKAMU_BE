from pydantic import BaseModel, Field
from typing import Optional, List, Any, Union
from datetime import date
from uuid import UUID

class SearchBaseResponse(BaseModel):
    status: str = Field(default="success")

class GenreItem(BaseModel):
    id: UUID
    name: str

class GenreListResponse(SearchBaseResponse):
    genres: List[GenreItem]

class ContentSearchItem(BaseModel):
    id: Union[int, UUID]
    type: str = Field(..., description="데이터 유형 (예: MOVIE, PERSON)")
    title: str
    poster_url: Optional[str] = None
    subtitle: Optional[str] = None

class ContentSearchResponse(SearchBaseResponse):
    items: List[ContentSearchItem]
    next_cursor: Union[int, str, UUID, None] = None

class PaginatedSearchResponse(SearchBaseResponse):
    items: List[Any]
    skip: int
    limit: int
    total_count: int

class PaginationMeta(BaseModel):
    total_count: int
    current_page: int
    page_size: int
    total_pages: int

class MovieSearchItem(BaseModel):
    id: UUID
    title: str
    poster_url: Optional[str] = None
    producing_year: Optional[int] = None
    nation: Optional[str] = None
    genres: List[str] = []

class MovieSearchResponse(SearchBaseResponse):
    items: List[MovieSearchItem]
    meta: PaginationMeta

class PersonSearchItem(BaseModel):
    id: UUID
    name: str
    profile_image: Optional[str] = None
    role: Optional[str] = None

class PersonSearchResponse(SearchBaseResponse):
    items: List[PersonSearchItem]
    meta: PaginationMeta

class UserSearchItem(BaseModel):
    id: UUID
    nickname: str
    tag: str
    profile_image_url: Optional[str] = None
    follower_count: int = 0
    is_following: bool = False

class UserSearchResponse(SearchBaseResponse):
    items: List[UserSearchItem]
    next_cursor: Optional[str] = None
    has_next: bool = False

class TrendSearchItem(BaseModel):
    rank: int
    keyword: str
    search_count: int

class TrendSearchResponse(SearchBaseResponse):
    stat_date: date
    items: List[TrendSearchItem]

class CustomSearchResponse(BaseModel):
    items: List[Any]
    next_cursor: Optional[str] = None
    is_fallback: bool = False
    message: Optional[str] = None

class CursorSearchResponse(SearchBaseResponse):
    items: List[Any]
    next_cursor: Optional[str] = None
    fallback: Optional[bool] = False
    message: Optional[str] = None
