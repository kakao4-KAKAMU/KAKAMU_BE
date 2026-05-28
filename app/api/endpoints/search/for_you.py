from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID

from app.db.session import get_db
from app.models import Post
from app.api.deps import verify_persona_ownership  # 구현한 소유권 검증 로직 임포트
from .utils import handle_search_request, get_search_pattern

router = APIRouter()

@router.get("/v1/search/for-you", tags=["Search - Tabs"])
def search_for_you(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(20, le=50),
    active_persona_id: UUID = Depends(verify_persona_ownership), # Query 파라미터를 받음과 동시에 소유권 검증 수행
    db: Session = Depends(get_db)
):
    handle_search_request(request, background_tasks, str(active_persona_id), q)
    search_pattern = get_search_pattern(q)

    query = db.query(Post).filter(
        Post.status == "ACTIVE",
        or_(Post.title.ilike(search_pattern), Post.content.ilike(search_pattern))
    ).order_by(Post.id.desc()).limit(100)

    candidates = query.all()
    
    if not candidates:
        return {"status": "success", "items": [], "fallback": True, "message": "결과가 없어 추천 항목을 제공합니다."}

    scored_results = []
    for post in candidates:
        text_accuracy = 100 if q in (post.title or "") else 50
        like_count = getattr(post, 'like_count', 0)
        popularity = min(like_count * 2, 100)
        persona_pref = 50 
        final_score = (text_accuracy * 0.4) + (popularity * 0.2) + (persona_pref * 0.4)
        scored_results.append({"post": post, "score": final_score})

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    items = [{"id": p["post"].id, "title": p["post"].title, "content": p["post"].content} for p in scored_results[:limit]]
    return {"status": "success", "items": items, "next_cursor": None}