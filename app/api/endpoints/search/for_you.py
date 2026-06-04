from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.models import Post
from app.api.deps import get_current_persona
from .utils import handle_search_request, get_search_pattern

router = APIRouter()

@router.get("/v1/search/for-you", tags=["Search - Tabs"])
def search_for_you(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    cursor: Optional[str] = Query(None, description="페이징 커서 (score_id)"),
    limit: int = Query(20, le=50),
    active_persona_id: UUID = Depends(get_current_persona),
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

    # 정렬: 점수 내림차순, ID 내림차순 (동점일 경우 최신순)
    scored_results.sort(key=lambda x: (x["score"], x["post"].id), reverse=True)

    # 커서 기반 페이징 적용
    if cursor:
        try:
            last_score_str, last_id_str = cursor.split("_")
            last_score = float(last_score_str)
            last_id = int(last_id_str)
            
            scored_results = [
                res for res in scored_results
                if res["score"] < last_score or (res["score"] == last_score and res["post"].id < last_id)
            ]
        except (ValueError, TypeError):
            pass # 잘못된 커서 형식은 무시

    paginated_results = scored_results[:limit]
    
    next_cursor = None
    if len(scored_results) > limit:
        last_item = paginated_results[-1]
        next_cursor = f"{last_item['score']}_{last_item['post'].id}"

    items = [{"id": p["post"].id, "title": p["post"].title, "content": p["post"].content} for p in paginated_results]
    return {"status": "success", "items": items, "next_cursor": next_cursor}