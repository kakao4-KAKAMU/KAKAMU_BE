from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자가 입력한 챗봇 메시지")
    session_id: str = Field(..., description="프론트엔드에서 생성 및 관리하는 채팅방 세션 ID")


class ChatListQuery(BaseModel):
    cursor: int | None = Field(default=None, ge=1, description="페이지 커서")
    limit: int = Field(default=20, ge=1, le=200, description="조회 개수")


class ChatHistoryQuery(BaseModel):
    cursor: int | None = Field(default=None, ge=1, description="페이지 커서")
    limit: int = Field(default=20, ge=1, le=200, description="조회 개수")