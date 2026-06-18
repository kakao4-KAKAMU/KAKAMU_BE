import logging
from uuid import UUID
from typing import Union  # [수정] UUID도 받을 수 있도록 추가
from sqlalchemy.orm import Session
from enum import Enum
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class ActionType(str, Enum):
    VIEW = "view"
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"

class RecommendationService:
    async def record_ml_relationship_log(
        self, 
        db: Session, 
        persona_id: UUID, 
        target_type: str, 
        target_id: Union[int, UUID, str],  # [수정] int -> UUID도 허용
        action: str, 
        is_undo: bool = False
    ):
        """
        [ML 로깅] 이벤트 소싱 패턴을 사용한 사용자 상호작용 기록 (ML 서버로 전송)
        백엔드 API(게시물 작성 등) 내부에서 발생하는 활동 로그를 추천(ML) 서버 API로 전달합니다.
        
        :param is_undo: True일 경우 사용자가 행동을 취소한 것으로 간주 (예: undo_create_post)
        """
        # 1. 로깅할 액션 이름 결정 (예: "create_post" -> 취소시 "undo_create_post")
        log_action = f"undo_{action}" if is_undo else action

        ML_API_URL = f"{settings.ML_API_BASE_URL}/api/recommendation/collect"
        
        payload = {
            "persona_id": str(persona_id),
            "target_type": target_type,
            "target_id": str(target_id) if isinstance(target_id, UUID) else target_id,
            "action": log_action
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(ML_API_URL, json=payload, timeout=3.0)
                response.raise_for_status()
        except Exception as e:
            logger.exception(f"[RecommendationLog] ML 서버로 로그 전송 실패: {e}")

# 싱글톤 인스턴스   
recommendation_service = RecommendationService()