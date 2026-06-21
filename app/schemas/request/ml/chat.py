from pydantic import BaseModel, Field


class MlChatListQuery(BaseModel):
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    cursor: int | None = Field(default=None, ge=1, description="페이지 커서")
    limit: int = Field(default=20, ge=1, le=200, description="조회 개수")


class MlChatHistoryQuery(BaseModel):
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    cursor: int | None = Field(default=None, ge=1, description="페이지 커서")
    limit: int = Field(default=20, ge=1, le=200, description="조회 개수")


class MlChatStreamRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    message: str = Field(..., min_length=1, description="사용자 메시지")
    persona_id: str | None = Field(default=None, description="페르소나 ID")
    session_id: str | None = Field(default=None, description="채팅 세션 ID")
    top_k: int = Field(default=10, ge=1, le=50, description="추천 후보 상위 K")
    max_toxicity: float = Field(default=0.7, ge=0.0, le=1.0, description="최대 독성 점수")
