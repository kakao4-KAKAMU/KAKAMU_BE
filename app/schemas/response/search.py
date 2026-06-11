from pydantic import BaseModel, Field
from typing import Optional, List, Any
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
    id: int
    title: str
    poster_url: Optional[str] = None

class ContentSearchResponse(SearchBaseResponse):
    items: List[ContentSearchItem]
    next_cursor: Optional[int] = None

class PaginatedSearchResponse(SearchBaseResponse):
    items: List[Any]
    skip: int
    limit: int
    total_count: int

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
