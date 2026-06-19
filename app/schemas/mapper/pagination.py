from typing import Optional, Union
from uuid import UUID

from app.schemas.base.pagination import CursorPaginationMeta, PagePaginationMeta


class PaginationMapper:
    @staticmethod
    def build_cursor_meta(
        *,
        total_count: int = 0,
        next_cursor: Optional[Union[int, UUID, str]] = None,
        has_next: bool = False,
        status: str = "success",
    ) -> CursorPaginationMeta:
        return CursorPaginationMeta(
            total_count=total_count,
            status=status,
            next_cursor=next_cursor,
            has_next=has_next,
        )

    @staticmethod
    def build_page_meta(
        *,
        total_count: int,
        current_page: int,
        page_size: int,
    ) -> PagePaginationMeta:
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        return PagePaginationMeta(
            total_count=total_count,
            current_page=current_page,
            page_size=page_size,
            total_pages=total_pages,
        )
