from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.ml import ChatMetadataType


class MlChatMetadata(BaseModel):
    type: ChatMetadataType | None = Field(default=None, description="메타데이터 타입")
    id: str | None = Field(default=None, description="메타데이터 대상 ID")


class MlChatMessage(BaseModel):
    id: int
    session_id: UUID
    user_id: str
    role: str
    content: str
    created_at: datetime
    reply_metadata: MlChatMetadata | None = None


class MlChatSession(BaseModel):
    session_id: UUID
    user_id: str
    persona_id: str | None
    started_at: datetime
    last_active: datetime
    metadata: dict = Field(default_factory=dict)


class MlChatSessionResponse(BaseModel):
    next_cursor: int | None
    has_more: bool
    messages: list[MlChatMessage]
