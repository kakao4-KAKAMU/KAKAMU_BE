from pydantic import BaseModel, Field
from typing import Any, Optional

class ChatCompletionResponse(BaseModel):
    """
    VLLM 서버의 생성 결과를 프론트엔드로 반환하는 응답 스키마입니다.
    """
    status: str = Field(default="success")
    data: Any = Field(..., description="챗봇 텍스트 생성 결과 데이터 (VLLM 응답)")