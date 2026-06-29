from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID
from typing import Optional

from app.schemas.request.post import LikeToggleRequest
from app.models import LikeLog, Post, Comment
from app.schemas.request.ml.ingest import (
    MlIngestCommentLikeEnvelope,
    MlIngestCommentLikePayload,
    MlIngestFeedLikeEnvelope,
    MlIngestFeedLikePayload,
)
from app.service.ml import ml_ingest_service
from app.service.ml.sync import safe_ml_call
from app.core.redis import redis_client
from app.service.like.like_count_service import (
    build_like_count_redis_key,
    clamp_like_count,
    REDIS_DECR_WITH_FLOOR_SCRIPT,
)
from app.service.notification.notification_service import notification_service
from app.models.notification import NotificationType

class LikeService:
    async def toggle_like(self, db: Session, req: LikeToggleRequest, user_id: UUID, persona_id: Optional[UUID]) -> tuple[bool, int]:
        """게시물 또는 댓글의 좋아요를 토글(Like/Unlike)하고 취향 가중치에 반영합니다."""
        if req.target_type == "POST":
            target = db.query(Post).filter(Post.id == req.target_id).first()
        elif req.target_type == "COMMENT":
            target = db.query(Comment).filter(Comment.id == req.target_id).first()
        else:
            raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_TARGET_TYPE", "message": "지원하지 않는 target_type 입니다."})
            
        if not target:
            raise HTTPException(status_code=404, detail={"code": "TARGET_NOT_FOUND", "message": "대상을 찾을 수 없습니다."})
            
        like_log = db.query(LikeLog).filter(LikeLog.user_id == user_id, LikeLog.target_type == req.target_type, LikeLog.target_id == req.target_id).first()
        
        if like_log:
            like_log.is_active = 0 if like_log.is_active == 1 else 1
            is_liked = like_log.is_active == 1
            
            # 취소할 때는 좋아요를 눌렀던 원래 페르소나의 ML 점수를 롤백해야 하므로 원래 페르소나 ID를 사용합니다.
            # 다시 좋아요를 누를 때는 현재 활성화된 페르소나 ID로 업데이트합니다.
            if is_liked:
                like_log.persona_id = persona_id
            else:
                persona_id = like_log.persona_id or persona_id
        else:
            like_log = LikeLog(user_id=user_id, persona_id=persona_id, target_type=req.target_type, target_id=req.target_id, is_active=1)
            db.add(like_log)
            is_liked = True
            
        db.commit()

        new_like_count = clamp_like_count(target.like_count or 0)
        try:
            redis_key = build_like_count_redis_key(req.target_type, req.target_id)
            
            # Redis에 키가 없을 경우 DB의 현재 좋아요 수로 초기화 (Cache Miss 현상 방지)
            await redis_client.setnx(redis_key, new_like_count)

            if is_liked:
                new_like_count = await redis_client.incr(redis_key)
            else:
                new_like_count = await redis_client.eval(REDIS_DECR_WITH_FLOOR_SCRIPT, 1, redis_key)
        except Exception as e:
            # Redis 실패 시 Fallback
            print(f"[Redis Error] Like stat update failed for {req.target_id}: {e}")
            new_like_count = clamp_like_count(new_like_count + (1 if is_liked else -1))
            
        if target.user_id != user_id:
            await self._sync_like_to_ml(
                req=req,
                user_id=user_id,
                persona_id=persona_id,
                is_liked=is_liked,
            )
            
            # 타인의 글에 좋아요를 누른 경우 알림 발송
            if is_liked:
                notification_service.create_notification(
                    db=db,
                    receiver_user_id=target.user_id,
                    sender_user_id=user_id,
                    sender_persona_id=persona_id,
                    type=NotificationType.LIKE,
                    target_type=req.target_type,
                    target_id=str(req.target_id),
                    message="님이 회원님의 콘텐츠를 좋아합니다."
                )

        # DB(target.like_count)에 즉시 업데이트하지 않고 Redis(sync_task)의 Bulk Update에 맡김

        return is_liked, new_like_count

    async def _sync_like_to_ml(
        self,
        *,
        req: LikeToggleRequest,
        user_id: UUID,
        persona_id: Optional[UUID],
        is_liked: bool,
    ) -> None:
        if req.target_type == "POST":
            envelope = MlIngestFeedLikeEnvelope(
                payload=MlIngestFeedLikePayload(
                    feed_id=str(req.target_id),
                    user_id=str(user_id),
                    persona_id=str(persona_id) if persona_id else None,
                    is_like=is_liked,
                )
            )
            await safe_ml_call("ingest feed like", lambda: ml_ingest_service.like_feed(envelope))
            return

        if req.target_type == "COMMENT":
            envelope = MlIngestCommentLikeEnvelope(
                payload=MlIngestCommentLikePayload(
                    comment_id=str(req.target_id),
                    user_id=str(user_id),
                    persona_id=str(persona_id) if persona_id else None,
                    is_like=is_liked,
                )
            )
            await safe_ml_call("ingest comment like", lambda: ml_ingest_service.like_comment(envelope))

like_service = LikeService()
