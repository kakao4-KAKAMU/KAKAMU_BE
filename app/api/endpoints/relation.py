from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Optional
from uuid import UUID

from app.db.session import get_db
from app.api.deps.auth import get_active_user
from app.schemas.response.relation import RelationResponse, FollowListResponse
from app.schemas.request.relation import BlockRequest
from app.service.relation.relation_service import relation_service
from app.models import Follow, User

router = APIRouter()

@router.post("/follows/{following_id}", response_model=RelationResponse)
async def follow_user(
    following_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
) -> Any:
    """현재 사용자로 특정 유저를 팔로우합니다."""
    if current_user.id == following_id:
        raise HTTPException(status_code=400, detail={"code": "CANNOT_FOLLOW_SELF", "message": "자기 자신을 팔로우할 수 없습니다."})
    return await relation_service.follow(db, follower_id=current_user.id, following_id=following_id)

@router.delete("/follows/{following_id}", response_model=RelationResponse)
async def unfollow_user(
    following_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
) -> Any:
    """특정 유저에 대한 팔로우를 해제합니다."""
    return await relation_service.unfollow(db, follower_id=current_user.id, following_id=following_id)

@router.post("/blocks/{blocked_id}", response_model=RelationResponse)
async def block_user(
    blocked_id: UUID,
    block_in: BlockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
) -> Any:
    """
    특정 유저를 차단합니다. 
    """
    if current_user.id == blocked_id:
        raise HTTPException(status_code=400, detail={"code": "CANNOT_BLOCK_SELF", "message": "자기 자신을 차단할 수 없습니다."})
    return await relation_service.block(
        db, blocker_id=current_user.id, blocked_id=blocked_id, level=block_in.level.value
    )

@router.delete("/blocks/{blocked_id}", response_model=RelationResponse)
async def unblock_user(
    blocked_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
) -> Any:
    """특정 유저에 대한 차단을 해제합니다."""
    return await relation_service.unblock(db, blocker_id=current_user.id, blocked_id=blocked_id)

@router.get("/{target_user_id}/followers", response_model=FollowListResponse)
def get_followers(
    target_user_id: UUID,
    cursor: Optional[UUID] = Query(None, description="마지막으로 조회한 팔로워의 유저 ID"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    특정 유저를 팔로우하는 사람(팔로워) 목록을 조회합니다.
    탈퇴(DELETED)한 유저는 목록에서 제외됩니다.
    """
    query = db.query(Follow).join(
        User, Follow.follower_id == User.id
    ).filter(
        Follow.following_id == target_user_id,
        User.status == "ACTIVE"
    )

    if cursor:
        query = query.filter(Follow.follower_id < cursor)

    follows = query.order_by(Follow.follower_id.desc()).limit(limit).all()

    items = []
    for f in follows:
        u = f.follower
        items.append({
            "id": u.id,
            "nickname": u.nickname,
            "username": u.username
        })

    next_cursor = items[-1]["id"] if items else None
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_next": len(items) == limit
    }

@router.get("/{target_user_id}/followings", response_model=FollowListResponse)
def get_followings(
    target_user_id: UUID,
    cursor: Optional[UUID] = Query(None, description="마지막으로 조회한 팔로잉 유저 ID"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    특정 유저가 팔로우하는 사람(팔로잉) 목록을 조회합니다.
    탈퇴(DELETED)한 유저는 목록에서 제외됩니다.
    """
    query = db.query(Follow).join(
        User, Follow.following_id == User.id
    ).filter(
        Follow.follower_id == target_user_id,
        User.status == "ACTIVE"
    )

    if cursor:
        query = query.filter(Follow.following_id < cursor)

    follows = query.order_by(Follow.following_id.desc()).limit(limit).all()

    items = []
    for f in follows:
        u = f.following_user
        items.append({
            "id": u.id,
            "nickname": u.nickname,
            "username": u.username
        })

    next_cursor = items[-1]["id"] if items else None
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_next": len(items) == limit
    }