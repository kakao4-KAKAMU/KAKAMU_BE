from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class MovieSimple(BaseModel):
    id: UUID
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None

class MentionSimple(BaseModel):
    id: UUID
    nickname: str
    tag: str

class PostResponse(BaseModel):
    id: int
    author_id: Optional[UUID] = None
    author: str
    author_nickname: str
    author_tag: Optional[str] = None
    author_image: Optional[str] = None
    title: str
    content: str
    image_urls: List[str]
    is_spoiler: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    movies: List[MovieSimple]
    hashtags: List[str]
    mentions: List[MentionSimple]
    like_count: int
    comment_count: int
    is_liked: bool
    is_following: bool

class PostListResponse(BaseModel):
    items: List[PostResponse]
    next_cursor: Optional[int] = None
    has_next: bool

class CommentItem(BaseModel):
    id: int
    parent_id: Optional[int]
    author_id: Optional[UUID]
    author: str
    author_image: Optional[str] = None
    author_tag: Optional[str] = None
    content: str
    is_spoiler: bool
    created_at: datetime
    like_count: int
    is_liked: bool
    hashtags: List[str] = []
    mentions: List[MentionSimple] = []

class PaginationMeta(BaseModel):
    total_count: int
    current_page: int
    page_size: int
    total_pages: int

class CommentListResponse(BaseModel):
    status: str = Field(default="success")
    items: List[CommentItem]
    meta: PaginationMeta

class CommentDetailResponse(BaseModel):
    id: int
    content: str
    like_count: int
    is_liked: bool
    hashtags: List[str] = []
    mentions: List[MentionSimple] = []

class LikeToggleResponse(BaseModel):
    status: str = Field(default="success")
    is_liked: bool = Field(..., description="좋아요 여부")
    like_count: int = Field(..., description="현재 좋아요 개수")
