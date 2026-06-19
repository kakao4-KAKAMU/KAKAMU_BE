from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.models import User
from app.api.deps.auth import get_optional_user
from app.service.search import search_service
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import PostSearchResponse

router = APIRouter()

@router.get(
    "/v1/search/live",
    tags=["Search - Tabs"],
    response_model=PostSearchResponse,
    summary="실시간 게시물 검색"
)
def search_live(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어 (부분 일치 검색)"),
    cursor: Optional[int] = Query(None, description="페이징 커서(ID)"),
    limit: int = Query(20, le=50),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    user_id = str(current_user.id) if current_user else "anonymous"
    handle_search_request(request, background_tasks, user_id, q)
    search_pattern = get_search_pattern(q)

    current_user_id = current_user.id if current_user else None
    return search_service.search_posts(
        db,
        search_pattern,
        cursor=cursor,
        limit=limit,
        current_user_id=current_user_id,
    )
