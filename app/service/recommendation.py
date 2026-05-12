import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.redis import redis_client
from app.models.models import EntityRelationshipLog

class RecommendationService:
    def __init__(self):
        # app.core.redis에서 생성한 비동기 클라이언트를 사용합니다.
        self.redis = redis_client

    async def record_ml_relationship_log(
        self, 
        db: Session, 
        profile_id: int, 
        target_type: str, 
        target_id: int, 
        action: str, 
        base_score: float, 
        is_undo: bool = False
    ):
        """
        [ML 로깅] 이벤트 소싱 패턴을 사용한 감성 점수 기록
        사용자가 행동(좋아요, 댓글 등)을 하거나 취소할 때 호출됩니다.
        삭제하지 않고 역수(음수)를 저장하여 알고리즘을 보정합니다.
        
        :param is_undo: True일 경우 사용자가 행동을 취소한 것으로 간주하고 점수를 역전시킴
        """
        # 1. 취소 이벤트일 경우 기존 점수의 역수(음수)를 취함
        final_score = -base_score if is_undo else base_score
        
        # 2. 로깅할 액션 이름 결정 (예: "like" -> 취소시 "undo_like")
        log_action = f"undo_{action}" if is_undo else action

        # 3. 새로운 로그를 무조건 추가 (Append-Only)
        new_log = EntityRelationshipLog(
            profile_id=profile_id,
            relation_type=log_action,
            target_type=target_type,
            target_id=target_id,
            sentiment_score=final_score,
            weight=1.0 # 기본 가중치
        )
        
        db.add(new_log)
        db.commit()
        
        # 참고: 이 로그는 타인에 의해 target_id 원본이 삭제되더라도 
        # FK 제약조건이 없으므로 이 로그 테이블에 안전하게 남아 추천 알고리즘 훈련에 사용됩니다.

    async def record_activity(self, persona_id: int, movie_id: int, action: str):
        """페르소나의 실시간 활동(클릭/시청)을 Redis Sorted Set에 기록"""
        activity_key = f"kakamu:persona:{persona_id}:activities"
        timestamp = int(time.time())
        
        # movie_id를 스코어(시간)와 함께 저장
        await self.redis.zadd(activity_key, {str(movie_id): timestamp})
        # 최신 50개만 남기고 삭제 (메모리 최적화)
        await self.redis.zremrangebyrank(activity_key, 0, -51)

    async def update_persona_preference(self, persona_id: int, genres: List[str]):
        """활동 기반으로 페르소나의 장르 선호도 점수를 증가시킴 (Hash)"""
        pref_key = f"kakamu:persona:{persona_id}:preferences"
        for genre in genres:
            await self.redis.hincrby(pref_key, genre, 1)

    async def get_persona_context(self, persona_id: int) -> Dict[str, Any]:
        """추천 엔진에 전달할 유저의 최신 상태(Context)를 한 번에 가져옴"""
        activity_key = f"kakamu:persona:{persona_id}:activities"
        pref_key = f"kakamu:persona:{persona_id}:preferences"

        # 최근 본 영화 리스트 (최신순 10개)
        recent_movies = await self.redis.zrevrange(activity_key, 0, 9)
        # 장르 선호도 전체 데이터
        preferences = await self.redis.hgetall(pref_key)

        return {
            "persona_id": persona_id,
            "recent_movie_ids": recent_movies,
            "genre_preferences": preferences
        }

# 싱글톤 인스턴스
recommendation_service = RecommendationService()