from pydantic import BaseModel, Field
from typing import Any

class ChatCompletionResponse(BaseModel):
    """
    VLLM 서버의 생성 결과를 프론트엔드로 반환하는 응답 스키마입니다.
    """
    status: str = Field(default="success")
    message: str = Field(default="정상적으로 챗봇에 대화가 전달 및 처리되었습니다.", description="전달 성공 메시지")
    session_id: str = Field(..., description="유지 중인 채팅방 세션 ID")
    data: Any = Field(..., description="챗봇 텍스트 생성 결과 데이터 (VLLM 응답)")