import logging
from uuid import UUID
import httpx
from app.schemas.request.log import ActivityLogCreate
from app.core.config import settings

logger = logging.getLogger(__name__)

class ActivityLogService:
    async def process_activity_log(self, persona_id: UUID, log_data: ActivityLogCreate):
        """
        프론트엔드로부터 받은 행동 로그를 추천(ML) 서버 API로 전달합니다.
        (백엔드는 DB에 직접 저장하지 않고 포워딩만 수행합니다)
        """
        ML_API_URL = f"{settings.ML_API_BASE_URL}/api/recommendation/collect"

        action = log_data.action.lower()
        target_type = log_data.target_type.lower()
        target_id = log_data.target_id
        
        payload = {
            "persona_id": str(persona_id),
            "target_type": target_type,
            "target_id": target_id,
            "action": action
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(ML_API_URL, json=payload, timeout=3.0)
                response.raise_for_status()
        except httpx.RequestError as e:
            logger.error(f"[ActivityLog] ML 서버로 로그 전송 실패: {e}")

activity_log_service = ActivityLogService()