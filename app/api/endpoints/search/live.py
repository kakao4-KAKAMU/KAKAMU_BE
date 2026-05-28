from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.models import Post
from app.api.deps import optional_verify_persona_ownership
from .utils import handle_search_request, get_search_pattern

router = APIRouter()

@router.get("/v1/search/live", tags=["Search - Tabs"])
def search_live(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어 (부분 일치 검색)"),
    cursor: Optional[int] = Query(None, description="페이징 커서(ID)"),
    limit: int = Query(20, le=50),
    active_persona_id: Optional[UUID] = Depends(optional_verify_persona_ownership),
    db: Session = Depends(get_db)
):
    handle_search_request(request, background_tasks, str(active_persona_id) if active_persona_id else None, q)
    search_pattern = get_search_pattern(q)

    query = db.query(Post).filter(
        Post.status == "ACTIVE",
        or_(Post.title.ilike(search_pattern), Post.content.ilike(search_pattern))
    )
    if cursor: query = query.filter(Post.id < cursor)
        
    posts = query.order_by(Post.id.desc()).limit(limit).all()
    items = [{"id": p.id, "title": p.title, "content": p.content} for p in posts]
    return {"status": "success", "items": items, "next_cursor": posts[-1].id if posts else None}