from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.base.comment import CommentItem
from app.schemas.base.post import PostItem
from app.schemas.base.pagination import PagePaginationMeta

PaginationMeta = PagePaginationMeta

PostResponse = PostItem


class PostListResponse(BaseModel):
    items: List[PostResponse]
    next_cursor: Optional[int] = None
    has_next: bool

CommentDetailResponse = CommentItem


class CommentListResponse(BaseModel):
    status: str = Field(default="success")
    items: List[CommentItem]
    meta: PaginationMeta

class LikeToggleResponse(BaseModel):
    status: str = Field(default="success")
    is_liked: bool = Field(..., description="좋아요 여부")
    like_count: int = Field(..., description="현재 좋아요 개수")


__all__ = [
    "PostResponse",
    "PostListResponse",
    "CommentDetailResponse",
    "CommentListResponse",
    "LikeToggleResponse",
]
