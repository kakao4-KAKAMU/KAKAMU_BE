from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.post import LikeToggleRequest
from app.models.models import LikeLog, Post, Comment
from app.service.recommendation import recommendation_service
from app.core.redis import redis_client

router = APIRouter()

@router.post("/likes")
async def toggle_like(req: LikeToggleRequest, db: Session = Depends(get_db), persona_id: int = Depends(get_current_persona)):
    """게시물 또는 댓글의 좋아요를 토글(Like/Unlike)하고 취향 가중치에 반영합니다."""
    # 타겟 조회
    if req.target_type == "POST":
        target = db.query(Post).filter(Post.id == req.target_id).first()
    elif req.target_type == "COMMENT":
        target = db.query(Comment).filter(Comment.id == req.target_id).first()
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 target_type 입니다.")
        
    if not target:
        raise HTTPException(status_code=404, detail="대상을 찾을 수 없습니다.")
        
    # 좋아요 로그 확인
    like_log = db.query(LikeLog).filter(LikeLog.persona_id == persona_id, LikeLog.target_type == req.target_type, LikeLog.target_id == req.target_id).first()
    
    if like_log:
        like_log.is_active = 0 if like_log.is_active == 1 else 1
        is_liked = like_log.is_active == 1
    else:
        like_log = LikeLog(persona_id=persona_id, target_type=req.target_type, target_id=req.target_id, is_active=1)
        db.add(like_log)
        is_liked = True
        
    db.commit()
    
    # 1. Redis 버퍼에 실시간 카운트 가감 (배치 동기화용)
    redis_key = f"kakamu:stat:{req.target_type.lower()}:{req.target_id}:likes"
    if is_liked:
        await redis_client.incr(redis_key)
    else:
        await redis_client.decr(redis_key)
        
    # 2. 추천 엔진 가중치 반영 (수동 피드백)
    # 본인이 작성한 글에 좋아요를 누르는 것은 인기도는 올리나 개인 취향에는 반영하지 않음
    if target.persona_id != persona_id:
        base_score = 1.0
        await recommendation_service.record_ml_relationship_log(db, persona_id, req.target_type, req.target_id, "like", base_score, is_undo=not is_liked)
        
    return {"status": "success", "is_liked": is_liked}