from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.logging import logger
from app.db.session import get_db
from app.models import User, Persona, PersonaStatus
from app.api.deps.auth import get_optional_user
from app.service.search import search_service
from app.service.search.for_you_search import for_you_search_service
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import PostSearchResponse

router = APIRouter()

@router.get(
    "/v1/search/for-you",
    tags=["Search - Tabs"],
    response_model=PostSearchResponse,
    summary="맞춤형 추천 검색"
)
async def search_for_you(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    cursor: Optional[str] = Query(None, description="페이징 커서 (score_id)"),
    limit: int = Query(20, le=50),
    current_user: Optional[User] = Depends(get_optional_user),
    x_persona_id: Optional[UUID] = Header(default=None, description="현재 활성화된 페르소나 ID"),
    db: Session = Depends(get_db)
):
    user_id = str(current_user.id) if current_user else "anonymous"
    handle_search_request(request, background_tasks, user_id, q)
    search_pattern = get_search_pattern(q)

    if not current_user:
        return _fallback_search(db, search_pattern, cursor, limit, current_user_id=None)

    try:
        persona_id = None
        if x_persona_id:
            persona = db.get(Persona, x_persona_id)
            if persona and persona.user_id == current_user.id and persona.status != PersonaStatus.DELETED:
                persona_id = persona.id

        ml_result = await for_you_search_service.search_for_you(
            db,
            user_id=current_user.id,
            persona_id=persona_id,
            query=q,
            limit=limit,
            search_pattern=search_pattern,
            current_user_id=current_user.id,
        )
        if ml_result is not None and ml_result.items:
            return ml_result
    except Exception as e:
        logger.warning(f"[ForYou Search] ML 서버 통신 실패, 기본 정렬로 Fallback을 실행합니다: {e}")

    return _fallback_search(db, search_pattern, cursor, limit, current_user_id=current_user.id)


def _fallback_search(
    db: Session,
    search_pattern: str,
    cursor: Optional[str],
    limit: int,
    current_user_id: Optional[UUID],
) -> PostSearchResponse:
    post_cursor = None
    if cursor:
        try:
            post_cursor = int(cursor)
        except (ValueError, TypeError):
            pass

    result = search_service.search_posts(
        db,
        search_pattern,
        cursor=post_cursor,
        limit=limit,
        current_user_id=current_user_id,
        order_by_likes=True,
        fallback=True,
    )
    if not result.items:
        return result.model_copy(update={"message": "검색 결과가 없습니다."})
    return result
