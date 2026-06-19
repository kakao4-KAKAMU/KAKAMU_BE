from pydantic import BaseModel, Field
from typing import Any

__all__ = ["ChatCompletionResponse"]


class ChatCompletionResponse(BaseModel):
    status: str = Field(default="success")
    message: str = Field(default="정상적으로 챗봇에 대화가 전달 및 처리되었습니다.", description="전달 성공 메시지")
    session_id: str = Field(..., description="유지 중인 채팅방 세션 ID")
    data: Any = Field(..., description="챗봇 텍스트 생성 결과 데이터 (VLLM 응답)")
