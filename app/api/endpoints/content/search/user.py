from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import or_, func, select
from uuid import UUID

from app.db.session import get_db
from app.models import User, Block
from app.api.deps.auth import get_optional_user
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import UserCursorSearchResponse

router = APIRouter()

@router.get(
    "/v1/search/user",
    tags=["Search - Tabs"],
    response_model=UserCursorSearchResponse,
    summary="유저 검색"
)
def search_user(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    cursor: Optional[str] = Query(None, description="페이징 커서 (nickname,id)"),
    limit: int = Query(20, le=50),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    user_id = str(current_user.id) if current_user else "anonymous"
    handle_search_request(request, background_tasks, user_id, q)
    search_pattern = get_search_pattern(q)

    # 닉네임/유저네임 단독 검색 및 '닉네임#태그' 형태의 복합 검색 지원
    query = db.query(User).filter(
        User.status == "ACTIVE",
        or_(
            User.username.ilike(search_pattern),
            User.nickname.ilike(search_pattern),
            func.concat(User.nickname, "#", User.tag).ilike(search_pattern)
        )
    )

    # 💡 로그인한 경우에만 차단 유저 필터링 적용
    if current_user:
        blocked_by_me = select(Block.blocked_id).where(Block.blocker_id == current_user.id)
        blocking_me = select(Block.blocker_id).where(Block.blocked_id == current_user.id)
        query = query.filter(User.id.notin_(blocked_by_me), User.id.notin_(blocking_me))
    
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
    items = [
        {
            "id": p.id,
            "username": p.username,
            "nickname": p.nickname,
            "tag": p.tag,
            "profile_image_url": p.profile_image_url,
        }
        for p in results
    ]

    next_cursor = None
    if len(results) == limit:
        last_item = results[-1]
        next_cursor = f"{last_item.nickname},{str(last_item.id)}"

    return {"status": "success", "items": items, "next_cursor": next_cursor}