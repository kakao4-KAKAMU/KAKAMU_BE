from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.models import Post
from app.api.deps import get_active_user
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import CursorSearchResponse

router = APIRouter()

@router.get("/v1/search/live", tags=["Search - Tabs"], response_model=CursorSearchResponse)
def search_live(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어 (부분 일치 검색)"),
    cursor: Optional[int] = Query(None, description="페이징 커서(ID)"),
    limit: int = Query(20, le=50),
    user = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    handle_search_request(request, background_tasks, None, q)
    search_pattern = get_search_pattern(q)

    query = db.query(Post).filter(
        Post.status == "ACTIVE",
        or_(Post.title.ilike(search_pattern), Post.content.ilike(search_pattern))
    )
    if cursor: query = query.filter(Post.id < cursor)
        
    posts = query.order_by(Post.id.desc()).limit(limit).all()
    items = [{"id": p.id, "title": p.title, "content": p.content} for p in posts]
    
    next_cursor = posts[-1].id if len(posts) == limit else None
    return {"status": "success", "items": items, "next_cursor": next_cursor}