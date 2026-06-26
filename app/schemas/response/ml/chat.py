from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.ml import ChatMetadataType
from app.schemas.base.movie import Movie
from app.schemas.base.post import PostItem


class MlChatMetadata(BaseModel):
    type: ChatMetadataType | None = Field(default=None, description="메타데이터 타입")
    id: str | None = Field(default=None, description="메타데이터 대상 ID")

class MlChatMetadataList(BaseModel):
    movie: list[MlChatMetadata] = Field(default_factory=list)
    feed: list[MlChatMetadata] = Field(default_factory=list)

class MlChatMessage(BaseModel):
    id: int
    session_id: UUID
    user_id: str
    role: str
    content: str
    created_at: datetime
    reply_metadata: MlChatMetadataList | None = None
    feed_list: list[PostItem] = Field(default_factory=list)
    movie_list: list[Movie] = Field(default_factory=list)


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
