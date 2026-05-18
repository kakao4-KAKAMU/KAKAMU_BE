from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.models.models import Post

router = APIRouter()

@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    persona_id: int = Depends(get_current_persona)
):
    """게시물을 서비스에서 즉시 숨김(Soft Delete) 처리합니다."""
    post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
    if not post:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다.")
        
    if post.persona_id != persona_id:
        raise HTTPException(status_code=403, detail="본인이 작성한 게시물만 삭제할 수 있습니다.")

    post.status = "INACTIVE"
    db.commit()
    return {"status": "success"}