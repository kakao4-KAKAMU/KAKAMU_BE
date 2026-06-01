from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID

from app.schemas.post.like import LikeToggleRequest
from app.models import LikeLog, Post, Comment
from app.service.recommendation.recommendation_service import recommendation_service
from app.core.redis import redis_client

class LikeService:
    async def toggle_like(self, db: Session, req: LikeToggleRequest, persona_id: UUID) -> tuple[bool, int]:
        """게시물 또는 댓글의 좋아요를 토글(Like/Unlike)하고 취향 가중치에 반영합니다."""
        if req.target_type == "POST":
            target = db.query(Post).filter(Post.id == req.target_id).first()
        elif req.target_type == "COMMENT":
            target = db.query(Comment).filter(Comment.id == req.target_id).first()
        else:
            raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_TARGET_TYPE", "message": "지원하지 않는 target_type 입니다."})
            
        if not target:
            raise HTTPException(status_code=404, detail={"code": "TARGET_NOT_FOUND", "message": "대상을 찾을 수 없습니다."})
            
        like_log = db.query(LikeLog).filter(LikeLog.persona_id == persona_id, LikeLog.target_type == req.target_type, LikeLog.target_id == req.target_id).first()
        
        if like_log:
            like_log.is_active = 0 if like_log.is_active == 1 else 1
            is_liked = like_log.is_active == 1
        else:
            like_log = LikeLog(persona_id=persona_id, target_type=req.target_type, target_id=req.target_id, is_active=1)
            db.add(like_log)
            is_liked = True
            
        db.commit()
        
        new_like_count = target.like_count
        try:
            redis_key = f"kakamu:stat:{req.target_type.lower()}:{req.target_id}:likes"
            
            # [Fix] Redis에 키가 없을 경우 DB의 현재 좋아요 수로 초기화 (Cache Miss로 인한 카운트 1 초기화 현상 방지)
            await redis_client.setnx(redis_key, target.like_count)

            if is_liked:
                new_like_count = await redis_client.incr(redis_key)
            else:
                new_like_count = await redis_client.decr(redis_key)
        except Exception as e:
            # Redis 통계 업데이트 실패 시에도 메인 좋아요 로직(DB 저장)은 완료되었으므로 에러를 삼킵니다.
            print(f"[Redis Error] Like stat update failed for {req.target_id}: {e}")
            # Redis 실패 시 Fallback 카운트
            new_like_count = target.like_count + (1 if is_liked else -1)
            
        if target.persona_id != persona_id:
            await recommendation_service.record_ml_relationship_log(db, persona_id, req.target_type, req.target_id, "like", 1.0, is_undo=not is_liked)
            
        return is_liked, new_like_count

like_service = LikeService()
