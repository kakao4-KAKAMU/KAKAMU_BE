from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.base.movie import Movie


class SaveToggleResponse(BaseModel):
    status: str = Field(default="success")
    is_saved: bool = Field(..., description="저장 여부")


class SavedMovieListResponse(BaseModel):
    status: str = Field(default="success")
    items: List[Movie]
    next_cursor: Optional[int] = Field(default=None, description="다음 페이지 SaveLog ID")
    has_next: bool = False


__all__ = [
    "SaveToggleResponse",
    "SavedMovieListResponse",
]
