from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.api.deps import get_current_persona, get_active_user
from app.models.user import User
from app.schemas.post.like import LikeToggleRequest
from app.service.like.like_service import like_service

router = APIRouter()

@router.post("/")
async def toggle_like(
    req: LikeToggleRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_active_user),
    persona_id: UUID = Depends(get_current_persona)
):
    """게시물 또는 댓글의 좋아요를 토글(Like/Unlike)하고 취향 가중치에 반영합니다."""
    is_liked, new_like_count = await like_service.toggle_like(db, req, current_user.id, persona_id)
    return {"status": "success", "is_liked": is_liked, "like_count": new_like_count}