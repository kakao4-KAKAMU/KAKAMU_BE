from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.api.deps.auth import get_active_user
from app.models.user import User
from app.schemas.response.common import SuccessResponse
from app.service.post.delete_post import post_delete_service

router = APIRouter()

@router.delete("/{post_id}", response_model=SuccessResponse)
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
    persona_id: UUID = Depends(get_current_persona)
):
    """게시물을 서비스에서 즉시 숨김(Soft Delete) 처리합니다."""
    await post_delete_service.delete_post(db, post_id, current_user.id, persona_id)
    return {"status": "success"}
