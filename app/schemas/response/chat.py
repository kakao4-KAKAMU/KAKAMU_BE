from pydantic import BaseModel, Field
from typing import Any

__all__ = ["ChatCompletionResponse"]


class ChatCompletionResponse(BaseModel):
    status: str = Field(default="success")
    data: Any = Field(..., description="챗봇 텍스트 생성 결과 데이터 (VLLM 응답)")
