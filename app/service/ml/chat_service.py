from collections.abc import AsyncIterator

from app.schemas.request.ml.chat import MlChatHistoryQuery, MlChatListQuery, MlChatStreamRequest
from app.schemas.response.ml.chat import MlChatSession, MlChatSessionResponse
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

    async def get_session_history(
        self,
        session_id: str,
        query: MlChatHistoryQuery,
    ) -> MlChatSessionResponse:
        response = await self._client.get(
            f"/chat/history/{session_id}",
            params=query.model_dump(mode="json", exclude_none=True),
        )
        return MlChatSessionResponse.model_validate(response.json())

    async def stream_chat(self, request: MlChatStreamRequest) -> AsyncIterator[bytes]:
        payload = request.model_dump(mode="json", exclude_none=True)
        async for chunk in self._client.stream_post("/chat/stream", json=payload, timeout=60.0):
            yield chunk


ml_chat_service = MlChatService()
