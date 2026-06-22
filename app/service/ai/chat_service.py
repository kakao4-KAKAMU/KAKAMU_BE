import json
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Persona, FavGenre, Genre
from app.core.redis import redis_client
from app.schemas.request.chat import ChatRequest
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

    async def prepare_chat_messages(
        self,
        db: Session,
        persona_id: UUID,
        session_id: str,
        message: str
    ) -> tuple[list[dict], str]:
        """
        페르소나 정보 및 선호 장르를 결합하여 시스템 프롬프트를 생성하고,
        Redis에서 세션 대화 히스토리를 로드하여 최종 VLLM 요청용 메시지 목록을 조립합니다.
        """
        # 1. 페르소나 정보 및 취향 조회 (시스템 프롬프트 생성용)
        persona = db.scalar(select(Persona).where(Persona.id == persona_id))
        if not persona:
            raise HTTPException(
                status_code=404, 
                detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없습니다."}
            )

        genres = db.query(Genre.genre_name).join(FavGenre, FavGenre.genre_id == Genre.id).filter(FavGenre.persona_id == persona_id).all()
        genre_names = [g[0] for g in genres]
        
        system_prompt = f"당신은 '{persona.nickname}'라는 사용자와 대화하는 영화 전문 AI 챗봇입니다."
        if genre_names:
            system_prompt += f" 이 사용자는 {', '.join(genre_names)} 장르를 좋아합니다. 사용자의 취향에 맞춰 친절하게 대답해주세요."

        # 2. Redis에서 이전 대화 기록(Context) 불러오기
        redis_key = f"kakamu:chat:history:{session_id}"
        history_data = await redis_client.get(redis_key)
        
        if history_data:
            messages = json.loads(history_data)
        else:
            messages = []

        # 3. 사용자의 새 메시지 추가 및 최종 VLLM 페이로드 구성
        user_message = {"role": "user", "content": message}
        messages.append(user_message)
        payload_messages = [{"role": "system", "content": system_prompt}] + messages

        return payload_messages, redis_key

    async def save_chat_history(self, redis_key: str, messages_without_system: list[dict], assistant_response: str) -> None:
        """
        어시스턴트의 최종 답변을 대화 히스토리에 추가하고 최근 20개 대화로 슬라이싱하여 Redis 캐시에 1시간(3600초) 보존합니다.
        """
        messages_without_system.append({"role": "assistant", "content": assistant_response})
        if len(messages_without_system) > 20:
            messages_without_system = messages_without_system[-20:]
            
        await redis_client.set(redis_key, json.dumps(messages_without_system), ex=3600)

chat_service = ChatService()
