import logging
import json
from uuid import UUID
from app.schemas.log import ActivityLogCreate
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

class ActivityLogService:
    async def process_activity_log(self, persona_id: UUID, log_data: ActivityLogCreate):
        """백그라운드에서 실행될 실제 로그 저장 및 분석 로직"""
        action = log_data.action.upper()
        target_type = log_data.target_type.upper()
        target_id = log_data.target_id
        
        score = 0.0
        if action == "VIEW":
            score = 0.5
        elif action == "SHARE":
            score = 2.0
        elif action == "HOVER" and log_data.duration_ms and log_data.duration_ms > 3000:
            score = 1.0
            
        if score > 0:
            # RDB에 직접 넣지 않고 Redis Queue에 담아 워커(ml_log_sync_worker)가 일괄 처리하도록 위임
            log_entry = {
                "persona_id": str(persona_id),
                "relation_type": action.lower(),
                "target_type": target_type,
                "target_id": target_id,
                "sentiment_score": score,
                "weight": 1.0
            }
            try:
                await redis_client.rpush("kakamu:queue:ml_logs", json.dumps(log_entry))
            except Exception as e:
                logger.error(f"[ActivityLog] Redis Queue Push Failed: {e}")

activity_log_service = ActivityLogService()