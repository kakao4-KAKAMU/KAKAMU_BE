import logging
import httpx
from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.core.config import settings
from app.models import Post, User
from app.api.deps import get_active_user, get_current_persona
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import CursorSearchResponse

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/v1/search/for-you", tags=["Search - Tabs"], response_model=CursorSearchResponse)
async def search_for_you(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    cursor: Optional[str] = Query(None, description="페이징 커서 (score_id)"),
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_active_user),
    active_persona_id: UUID = Depends(get_current_persona),
    db: Session = Depends(get_db)
):
    handle_search_request(request, background_tasks, str(current_user.id), q)
    search_pattern = get_search_pattern(q)

    # -------------------------------------------------------------------------
    # [V2: ML 서버 추천 결과 호출] 
    # 프론트엔드의 검색 요청을 받아 ML 서버로 전달하고,
    # 계산된 맞춤 검색 결과를 그대로 반환하는 API Gateway 역할을 수행합니다.
    # -------------------------------------------------------------------------
    ML_API_URL = f"{settings.ML_API_BASE_URL}/api/recommendation/search/posts"
    params = {"persona_id": str(active_persona_id), "q": q, "limit": limit}
    if cursor:
        params["cursor"] = cursor
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(ML_API_URL, params=params, timeout=3.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"[ForYou Search] ML 서버 통신 실패, 기본 정렬로 Fallback을 실행합니다: {e}")

    # -------------------------------------------------------------------------
    # [V1: 기존 규칙 기반(Heuristic) 추천 로직 주석 처리]
    # -------------------------------------------------------------------------
    """
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

    scored_results.sort(key=lambda x: (x["score"], x["post"].id), reverse=True)

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
            pass

    paginated_results = scored_results[:limit]
    
    next_cursor = None
    if len(scored_results) > limit:
        last_item = paginated_results[-1]
        next_cursor = f"{last_item['score']}_{last_item['post'].id}"

    items = [{"id": p["post"].id, "title": p["post"].title, "content": p["post"].content} for p in paginated_results]
    return {"status": "success", "items": items, "next_cursor": next_cursor}
    """

    # [V2 Fallback 로직]
    query = db.query(Post).filter(
        Post.status == "ACTIVE",
        or_(Post.title.ilike(search_pattern), Post.content.ilike(search_pattern))
    )
    if cursor:
        try:
            query = query.filter(Post.id < int(cursor))
        except (ValueError, TypeError):
            pass
            
    # 추천 결과가 없으므로 좋아요 높은 순서 위주로 기본 서빙
    paginated_results = query.order_by(Post.like_count.desc(), Post.id.desc()).limit(limit).all()
    
    if not paginated_results:
        return {"status": "success", "items": [], "fallback": True, "message": "결과가 없어 추천 항목을 제공합니다."}
        
    next_cursor = str(paginated_results[-1].id) if len(paginated_results) == limit else None
    items = [{"id": p.id, "title": p.title, "content": p.content} for p in paginated_results]
    
    return {"status": "success", "items": items, "next_cursor": next_cursor}