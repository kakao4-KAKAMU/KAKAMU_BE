from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Optional

from app.db.session import get_db
from app.api.deps.persona import get_current_persona
from app.schemas.relation import RelationResponse, BlockRequest, FollowListResponse
from app.service.relation import relation_service
from app.models import Follow, Persona

router = APIRouter()

@router.post("/follows/{following_id}", response_model=RelationResponse)
async def follow_persona(
    following_id: int,
    db: Session = Depends(get_db),
    current_persona_id: int = Depends(get_current_persona)
) -> Any:
    """현재 활성화된 페르소나로 특정 페르소나를 팔로우합니다."""
    if current_persona_id == following_id:
        raise HTTPException(status_code=400, detail="자기 자신을 팔로우할 수 없습니다.")
    return await relation_service.follow(db, follower_id=current_persona_id, following_id=following_id)

@router.delete("/follows/{following_id}", response_model=RelationResponse)
async def unfollow_persona(
    following_id: int,
    db: Session = Depends(get_db),
    current_persona_id: int = Depends(get_current_persona)
) -> Any:
    """특정 페르소나에 대한 팔로우를 해제합니다."""
    return await relation_service.unfollow(db, follower_id=current_persona_id, following_id=following_id)

@router.post("/blocks/{blocked_id}", response_model=RelationResponse)
async def block_persona(
    blocked_id: int,
    block_in: BlockRequest,
    db: Session = Depends(get_db),
    current_persona_id: int = Depends(get_current_persona)
) -> Any:
    """
    특정 페르소나를 차단합니다. 
    레벨(PERSONA, USER)에 따라 단일 페르소나 또는 계정 단위 차단이 수행됩니다.
    """
    if current_persona_id == blocked_id:
        raise HTTPException(status_code=400, detail="자기 자신을 차단할 수 없습니다.")
    return await relation_service.block(
        db, blocker_id=current_persona_id, blocked_id=blocked_id, level=block_in.level.value
    )

@router.delete("/blocks/{blocked_id}", response_model=RelationResponse)
async def unblock_persona(
    blocked_id: int,
    db: Session = Depends(get_db),
    current_persona_id: int = Depends(get_current_persona)
) -> Any:
    """특정 페르소나에 대한 차단을 해제합니다."""
    return await relation_service.unblock(db, blocker_id=current_persona_id, blocked_id=blocked_id)

@router.get("/{target_persona_id}/followers", response_model=FollowListResponse)
def get_followers(
    target_persona_id: int,
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 팔로워의 페르소나 ID"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    특정 페르소나를 팔로우하는 사람(팔로워) 목록을 조회합니다.
    탈퇴(DELETED)한 페르소나는 목록에서 제외됩니다.
    """
    query = db.query(Follow).join(
        Persona, Follow.follower_id == Persona.id
    ).filter(
        Follow.following_id == target_persona_id,
        Persona.status == "ACTIVE"
    )

    if cursor:
        query = query.filter(Follow.follower_id < cursor)

    follows = query.order_by(Follow.follower_id.desc()).limit(limit).all()

    items = []
    for f in follows:
        p = f.follower
        items.append({
            "id": p.id,
            "nickname": p.nickname,
            "tag": p.tag,
            "profile_image_url": p.profile_image_url
        })

    next_cursor = items[-1]["id"] if items else None
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_next": len(items) == limit
    }

@router.get("/{target_persona_id}/followings", response_model=FollowListResponse)
def get_followings(
    target_persona_id: int,
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 팔로잉 페르소나 ID"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    특정 페르소나가 팔로우하는 사람(팔로잉) 목록을 조회합니다.
    탈퇴(DELETED)한 페르소나는 목록에서 제외됩니다.
    """
    query = db.query(Follow).join(
        Persona, Follow.following_id == Persona.id
    ).filter(
        Follow.follower_id == target_persona_id,
        Persona.status == "ACTIVE"
    )

    if cursor:
        query = query.filter(Follow.following_id < cursor)

    follows = query.order_by(Follow.following_id.desc()).limit(limit).all()

    items = []
    for f in follows:
        p = f.following_persona
        items.append({
            "id": p.id,
            "nickname": p.nickname,
            "tag": p.tag,
            "profile_image_url": p.profile_image_url
        })

    next_cursor = items[-1]["id"] if items else None
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_next": len(items) == limit
    }