from pydantic import BaseModel, Field
from typing import Any

from app.schemas.response.ml.chat import (
    MlChatMessage,
    MlChatMetadata,
    MlChatSession,
    MlChatSessionResponse,
)

__all__ = [
    "ChatCompletionResponse",
    "ChatMessage",
    "ChatMetadata",
    "ChatSession",
    "ChatSessionHistoryResponse",
]

ChatMessage = MlChatMessage
ChatMetadata = MlChatMetadata
ChatSession = MlChatSession
ChatSessionHistoryResponse = MlChatSessionResponse


class ChatCompletionResponse(BaseModel):
    status: str = Field(default="success")
    data: Any = Field(..., description="챗봇 텍스트 생성 결과 데이터 (VLLM 응답)")
