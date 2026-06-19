from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class CursorPaginationMeta(BaseModel):
    total_count: int
    status: str = Field(default="success")
    next_cursor: Optional[Union[int, UUID, str]] = None
    has_next: bool


class PagePaginationMeta(BaseModel):
    total_count: int
    current_page: int
    page_size: int
    total_pages: int
