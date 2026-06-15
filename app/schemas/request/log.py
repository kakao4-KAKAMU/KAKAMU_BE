from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ActivityLogCreate(BaseModel):
    target_type: str = Field(..., description="타겟 유형 (예: MOVIE, POST, GENRE, PEOPLE)")
    target_id: int = Field(..., description="타겟 ID")
    action: str = Field(..., description="사용자 행동/관계 유형 (예: VIEW, HOVER, SHARE) - DB의 relation_type에 매핑")
    duration_ms: Optional[int] = Field(default=None, description="체류 시간(밀리초), 필요한 경우 가중치(weight) 계산에 활용")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="기타 추가 메타데이터")
