from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.api.deps.persona import get_current_persona
from app.schemas.relation import RelationResponse, BlockRequest
from app.service.relation import relation_service

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