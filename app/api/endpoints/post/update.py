from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.post.update import PostUpdate
from app.service.post.update_post import post_update_service

router = APIRouter()

@router.put("/{post_id}")
async def update_post(
    post_id: int,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    persona_id: UUID = Depends(get_current_persona)
):
    """게시물을 수정합니다. 본문이 수정되면 '수정됨' 표시를 위한 갱신이 일어납니다."""
    updated_post_id = await post_update_service.update_post(db, post_id, post_in, persona_id)
    return {"status": "success", "post_id": updated_post_id}