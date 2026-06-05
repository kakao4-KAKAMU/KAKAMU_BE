from pydantic import BaseModel, Field
from typing import Optional

class ActivityLogCreate(BaseModel):
    target_type: str = Field(..., description="타겟 유형 (예: MOVIE, POST, GENRE, PEOPLE)")
    target_id: int = Field(..., description="타겟 ID")
    action: str = Field(..., description="사용자 행동 (예: VIEW, HOVER, SHARE)")
    duration_ms: Optional[int] = Field(None, description="체류 시간(밀리초)")