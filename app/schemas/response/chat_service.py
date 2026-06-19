import json
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID

from app.models import Persona, FavGenre, Genre
from app.core.redis import redis_client
from app.core.config import settings
from app.schemas.request.chat import ChatRequest

class ChatService:
    async def generate_chat_response(self, db: Session, persona_id: UUID, req: ChatRequest) -> str:
        # 1. 페르소나 정보 및 취향 조회 (시스템 프롬프트 생성용)
        persona = db.scalar(select(Persona).where(Persona.id == persona_id))
        if not persona:
            raise HTTPException(status_code=404, detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없습니다."})

        genres = db.query(Genre.genre_name).join(FavGenre, FavGenre.genre_id == Genre.id).filter(FavGenre.persona_id == persona_id).all()
        genre_names = [g[0] for g in genres]
        
        system_prompt = f"당신은 '{persona.nickname}'라는 사용자와 대화하는 영화 전문 AI 챗봇입니다."
        if genre_names:
            system_prompt += f" 이 사용자는 {', '.join(genre_names)} 장르를 좋아합니다. 사용자의 취향에 맞춰 친절하게 대답해주세요."

        # 2. Redis에서 이전 대화 기록(Context) 불러오기
        redis_key = f"kakamu:chat:history:{req.session_id}"
        history_data = await redis_client.get(redis_key)
        
        if history_data:
            messages = json.loads(history_data)
        else:
            messages = []

        # 3. 사용자의 새 메시지 추가 및 최종 VLLM 페이로드 구성
        user_message = {"role": "user", "content": req.message}
        messages.append(user_message)
        payload_messages = [{"role": "system", "content": system_prompt}] + messages

        # 4. 외부 VLLM 서버와 통신 (OpenAI API 포맷 호환 가정)
        vllm_api_url = f"{settings.ML_API_BASE_URL}/v1/chat/completions"
        assistant_content = ""
        
        try:
            if not settings.ML_API_BASE_URL:
                # ML 서버가 꺼져있거나 주소가 없을 때를 대비한 Fallback Mock 데이터
                assistant_content = f"'{req.message}'에 대한 답변입니다. (현재 백엔드에 ML_API_BASE_URL 환경변수가 설정되지 않아 Mock 데이터를 반환합니다.)"
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        vllm_api_url, 
                        json={"model": "vllm-model", "messages": payload_messages, "max_tokens": 1024, "temperature": 0.7},
                        timeout=30.0
                    )
                    response.raise_for_status()
                    result_json = response.json()
                    assistant_content = result_json["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[VLLM API Error] {e}")
            raise HTTPException(status_code=503, detail={"code": "ML_SERVER_UNAVAILABLE", "message": "현재 AI 챗봇 서버와 연결할 수 없습니다."})

        # 5. 챗봇의 응답을 대화 기록에 추가하고 Redis에 저장 (최근 20개 대화만 유지하여 메모리 및 컨텍스트 길이 최적화)
        messages.append({"role": "assistant", "content": assistant_content})
        if len(messages) > 20:
            messages = messages[-20:]
            
        await redis_client.set(redis_key, json.dumps(messages), ex=3600) # 대화 세션 유효기간: 1시간

        return assistant_content

chat_service = ChatService()