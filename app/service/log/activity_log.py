import logging
from uuid import UUID
from app.schemas.request.log import ActivityLogCreate
from app.models import EntityRelationshipLog
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class ActivityLogService:
    async def process_activity_log(self, persona_id: UUID, log_data: ActivityLogCreate):
        """백그라운드에서 실행될 실제 로그 저장 및 분석 로직"""
        action = log_data.action.lower()
        target_type = log_data.target_type.lower()
        target_id = log_data.target_id
        
        # score = 0.0
        # if action == "view":
        #     score = 0.5
        # elif action == "share":
        #     score = 2.0
        # elif action == "hover" and log_data.duration_ms and log_data.duration_ms > 3000:
        #     score = 1.0
            
        # if score > 0:
        # Redis Queue를 거치지 않고 바로 RDB에 직접 적재
        db = SessionLocal()
        try:
            log_entry = EntityRelationshipLog(
                persona_id=persona_id,
                relation_type=action,
                target_type=target_type,
                target_id=target_id,
                # sentiment_score=score,
                weight=1.0
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[ActivityLog] Direct DB Insert Failed: {e}")
        finally:
            db.close()

activity_log_service = ActivityLogService()