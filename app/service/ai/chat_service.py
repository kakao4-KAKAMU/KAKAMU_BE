from uuid import UUID

from app.schemas.request.ml.chat import MlChatHistoryQuery, MlChatListQuery
from app.schemas.response.chat import ChatSession, ChatSessionHistoryResponse
from app.service.ml import ml_chat_service

class ChatService:
    async def list_sessions(
        self,
        user_id: UUID,
        *,
        cursor: int | None = None,
        limit: int = 20,
    ) -> list[ChatSession]:
        return await ml_chat_service.list_sessions(
            MlChatListQuery(
                user_id=str(user_id),
                cursor=cursor,
                limit=limit,
            )
        )

    async def get_session_history(
        self,
        user_id: UUID,
        session_id: str,
        *,
        cursor: int | None = None,
        limit: int = 20,
    ) -> ChatSessionHistoryResponse:
        return await ml_chat_service.get_session_history(
            session_id,
            MlChatHistoryQuery(
                user_id=str(user_id),
                cursor=cursor,
                limit=limit,
            ),
        )


chat_service = ChatService()
