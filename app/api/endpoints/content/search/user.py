from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import or_, func, select
from uuid import UUID

from app.db.session import get_db
from app.models import User, Block
from app.api.deps import get_active_user
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import CursorSearchResponse

router = APIRouter()

@router.get("/v1/search/user", tags=["Search - Tabs"], response_model=CursorSearchResponse)
def search_user(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    cursor: Optional[str] = Query(None, description="페이징 커서 (nickname,id)"),
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    handle_search_request(request, background_tasks, str(current_user.id), q)
    search_pattern = get_search_pattern(q)

    # 💡 차단 유저 필터링: 내가 차단했거나 나를 차단한 유저의 ID 목록 추출
    blocked_by_me = select(Block.blocked_id).where(Block.blocker_id == current_user.id)
    blocking_me = select(Block.blocker_id).where(Block.blocked_id == current_user.id)

    # 닉네임/유저네임 단독 검색 및 '닉네임#태그' 형태의 복합 검색 지원
    query = db.query(User).filter(
        User.status == "ACTIVE",
        User.id.notin_(blocked_by_me),
        User.id.notin_(blocking_me),
        or_(
            User.username.ilike(search_pattern),
            User.nickname.ilike(search_pattern),
            func.concat(User.nickname, "#", User.tag).ilike(search_pattern)
        )
    )
    
    # 커서 기반 페이징 적용
    if cursor:
        try:
            last_nickname, last_id_str = cursor.rsplit(',', 1)
            last_id = UUID(last_id_str)
            query = query.filter(
                or_(
                    User.nickname > last_nickname,
                    (User.nickname == last_nickname) & (User.id < last_id)
                )
            )
        except (ValueError, TypeError):
            # 잘못된 커서 형식은 무시하고 첫 페이지부터 조회
            pass

    # 결정적 정렬 보장: 닉네임 오름차순 기본, 고유 ID로 2차 정렬
    query = query.order_by(User.nickname.asc(), User.id.desc())
    
    results = query.limit(limit).all()
    items = [{"id": str(p.id), "username": p.username, "nickname": p.nickname, "tag": p.tag, "profile_image_url": p.profile_image_url} for p in results]

    next_cursor = None
    if len(results) == limit:
        last_item = results[-1]
        next_cursor = f"{last_item.nickname},{str(last_item.id)}"

    return {"status": "success", "items": items, "next_cursor": next_cursor}