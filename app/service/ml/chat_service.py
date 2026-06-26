from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.request.ml.chat import MlChatHistoryQuery, MlChatListQuery, MlChatStreamRequest
from app.schemas.response.ml.chat import MlChatSession, MlChatSessionResponse
from app.service.ml.chat_stream_enrichment import ChatStreamEnrichmentService
from app.service.ml.client import MlApiClient, ml_api_client


class MlChatService:
    def __init__(self, client: MlApiClient | None = None):
        self._client = client or ml_api_client

    async def list_sessions(self, query: MlChatListQuery) -> list[MlChatSession]:
        response = await self._client.get(
            "/chat/list",
            params=query.model_dump(mode="json", exclude_none=True),
        )
        return [MlChatSession.model_validate(item) for item in response.json()]

    async def list_sessions_for_user(
        self,
        user_id: UUID,
        *,
        cursor: int | None = None,
        limit: int = 20,
    ) -> list[MlChatSession]:
        return await self.list_sessions(
            MlChatListQuery(
                user_id=str(user_id),
                cursor=cursor,
                limit=limit,
            )
        )

    async def get_session_history(
        self,
        db: Session,
        user_id: UUID,
        session_id: str,
        query: MlChatHistoryQuery,
    ) -> MlChatSessionResponse:
        response = await self._client.get(
            f"/chat/history/{session_id}",
            params=query.model_dump(mode="json", exclude_none=True),
        )
        session_response = MlChatSessionResponse.model_validate(response.json())
        enricher = ChatStreamEnrichmentService(db, user_id)
        return enricher.enrich_session_response(session_response)

    async def get_session_history_for_user(
        self,
        db: Session,
        user_id: UUID,
        session_id: str,
        *,
        cursor: int | None = None,
        limit: int = 20,
    ) -> MlChatSessionResponse:
        return await self.get_session_history(
            db,
            user_id,
            session_id,
            MlChatHistoryQuery(
                user_id=str(user_id),
                cursor=cursor,
                limit=limit,
            ),
        )

    async def _stream_chat_raw(self, request: MlChatStreamRequest) -> AsyncIterator[bytes]:
        payload = request.model_dump(mode="json", exclude_none=True)
        async for chunk in self._client.stream_post("/chat/stream", json=payload, timeout=60.0):
            yield chunk

    async def stream_chat(
        self,
        db: Session,
        user_id: UUID,
        request: MlChatStreamRequest,
    ) -> AsyncIterator[bytes]:
        enricher = ChatStreamEnrichmentService(db, user_id)
        async for chunk in enricher.enrich_stream(self._stream_chat_raw(request)):
            yield chunk


ml_chat_service = MlChatService()
