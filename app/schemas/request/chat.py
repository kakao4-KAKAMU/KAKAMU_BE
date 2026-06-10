from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자가 입력한 챗봇 메시지")
    
    history: list[dict] = Field(default=[], description="이전 대화 내역 (role, content 구조)")