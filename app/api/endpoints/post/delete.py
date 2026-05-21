from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.models import Post, Comment, LikeLog, PostMovie
from app.service.recommendation import recommendation_service

router = APIRouter()

@router.delete("/{post_id}")
async def delete_post(
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
    
    # 게시물 삭제 시 연관된 하위 댓글들도 모두 비활성화 처리 (Soft Delete)
    db.query(Comment).filter(Comment.post_id == post.id).update({"status": "INACTIVE"})
    
    # 게시물에 달린 좋아요 무효화
    db.query(LikeLog).filter(LikeLog.target_type == "POST", LikeLog.target_id == post.id).update({"is_active": 0})
    
    # 게시물 삭제 시 추천 엔진 가중치 롤백 (작성 시 부여된 2.0 가중치 회수)
    post_movies = db.query(PostMovie).filter(PostMovie.post_id == post.id).all()
    for pm in post_movies:
        await recommendation_service.record_ml_relationship_log(
            db, persona_id, "MOVIE", pm.movie_id, "create_post", base_score=2.0, is_undo=True
        )

    db.commit()
    return {"status": "success"}
