from app.core.redis import redis_client

class PersonaService:
    def __init__(self):
        self.redis = redis_client

    async def switch_persona(self, user_id: int, persona_id: int):
        """
        유저의 현재 활성 페르소나를 변경합니다.
        """
        key = f"kakamu:user:{user_id}:current_persona"
        # Redis에 유저별 현재 페르소나 ID 저장 (예: 24시간 유지)
        await self.redis.set(key, persona_id, ex=86400)
        return {"status": "success", "active_persona_id": persona_id}

    async def get_active_persona_id(self, user_id: int):
        """
        현재 유저가 어떤 페르소나로 접속 중인지 가져옵니다.
        """
        key = f"kakamu:user:{user_id}:current_persona"
        persona_id = await self.redis.get(key)
        return int(persona_id) if persona_id else None

persona_service = PersonaService()