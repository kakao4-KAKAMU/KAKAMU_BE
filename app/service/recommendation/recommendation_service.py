import time
import json
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models import EntityRelationshipLog
from enum import Enum

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
        target_id: int, 
        action: str, 
        is_undo: bool = False
    ):
        """
        [ML 로깅] 이벤트 소싱 패턴을 사용한 사용자 상호작용 기록
        사용자가 행동(태그, 좋아요 등)을 하거나 취소할 때 원본 액션만 기록합니다.
        실제 가중치 판별 및 점수 계산은 추천(ML) 서버에서 배치로 수행합니다.
        
        :param is_undo: True일 경우 사용자가 행동을 취소한 것으로 간주 (예: undo_create_post)
        """
        # 1. 로깅할 액션 이름 결정 (예: "create_post" -> 취소시 "undo_create_post")
        log_action = f"undo_{action}" if is_undo else action

        # 2. 즉시 DB에 적재 (Direct Insert)
        new_log = EntityRelationshipLog(
            persona_id=persona_id,
            relation_type=log_action,
            target_type=target_type,
            target_id=target_id
        )
        db.add(new_log)
        db.commit()

        # 참고: 이 로그는 타인에 의해 target_id 원본이 삭제되더라도 
        # FK 제약조건이 없으므로 이 로그 테이블에 안전하게 남아 추천 알고리즘 훈련에 사용됩니다.

# 싱글톤 인스턴스
recommendation_service = RecommendationService()