from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import or_, func
from uuid import UUID

from app.db.session import get_db
from app.models import Persona
from .utils import handle_search_request, get_search_pattern

router = APIRouter()

@router.get("/v1/search/user", tags=["Search - Tabs"])
def search_user(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    cursor: Optional[str] = Query(None, description="페이징 커서 (nickname,id)"),
    limit: int = Query(20, le=50),
    x_persona_id: Optional[UUID] = Header(None, alias="X-Persona-Id", description="현재 활성화된 페르소나 ID"),
    db: Session = Depends(get_db)
):
    handle_search_request(request, background_tasks, str(x_persona_id) if x_persona_id else None, q)
    search_pattern = get_search_pattern(q)

    # 닉네임 단독 검색 및 '닉네임#태그' 형태의 복합 검색 모두 지원
    query = db.query(Persona).filter(
        Persona.status == "ACTIVE",
        or_(
            Persona.nickname.ilike(search_pattern),
            func.concat(Persona.nickname, "#", Persona.tag).ilike(search_pattern)
        )
    )
    
    # 커서 기반 페이징 적용
    if cursor:
        try:
            last_nickname, last_id_str = cursor.rsplit(',', 1)
            last_id = UUID(last_id_str)
            # (nickname > last_nickname) OR (nickname = last_nickname AND id < last_id)
            query = query.filter(
                or_(
                    Persona.nickname > last_nickname,
                    (Persona.nickname == last_nickname) & (Persona.id < last_id)
                )
            )
        except (ValueError, TypeError):
            # 잘못된 커서 형식은 무시하고 첫 페이지부터 조회
            pass

    # 결정적 정렬 보장: 닉네임 오름차순을 기본으로 하되, 고유 ID로 2차 정렬
    query = query.order_by(Persona.nickname.asc(), Persona.id.desc())
    
    results = query.limit(limit).all()
    items = [{"id": str(p.id), "nickname": p.nickname, "tag": p.tag} for p in results]

    next_cursor = None
    if len(results) == limit:
        last_item = results[-1]
        next_cursor = f"{last_item.nickname},{str(last_item.id)}"

    return {"status": "success", "items": items, "next_cursor": next_cursor}