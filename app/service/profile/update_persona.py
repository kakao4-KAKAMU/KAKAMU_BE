from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models import Persona, FavMovie, FavGenre, FavPeople
from app.schemas.profile import PersonaEdit
from app.service.profile.create_persona import PersonaCreateService
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class PersonaUpdateService:

    @staticmethod
    async def update_persona(
        db: Session,
        user_id: UUID,
        persona_id: UUID,
        persona_data: PersonaEdit
    ) -> Persona:
        with tracer.start_as_current_span("persona.update") as span:
            span.set_attribute("user_id", str(user_id))
            span.set_attribute("persona_id", str(persona_id))

            # 1. 페르소나 존재 여부 및 본인 소유 확인
            stmt = select(Persona).where(
                and_(
                    Persona.id == persona_id,
                    Persona.user_id == user_id,
                    Persona.status == "ACTIVE"
                )
            )
            persona = db.scalar(stmt)

            if not persona:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없거나 권한이 없습니다."}
                )

            # 2. 닉네임 변경 요청 시 처리 (태그 재발급 포함)
            if persona_data.nickname is not None:
                if persona_data.nickname == persona.nickname:
                    raise HTTPException(
                        status_code=400,
                        detail={"code": "SAME_NICKNAME", "message": "기존과 동일한 닉네임입니다."}
                    )
                
                # 새 닉네임에 부여할 유니크 태그 발급 (최대 10회 재시도)
                tag = None
                MAX_RETRY = 10
                with tracer.start_as_current_span("persona.generate_new_tag"):
                    for _ in range(MAX_RETRY):
                        candidate_tag = PersonaCreateService.generate_random_tag()
                        exist_stmt = select(Persona).where(
                            and_(Persona.nickname == persona_data.nickname, Persona.tag == candidate_tag)
                        )
                        if not db.scalar(exist_stmt):
                            tag = candidate_tag
                            break
                    
                    if tag is None:
                        raise HTTPException(
                            status_code=500,
                            detail={"code": "TAG_GENERATION_FAILED", "message": "새로운 태그 발급에 실패했습니다."}
                        )
                
                persona.nickname = persona_data.nickname
                persona.tag = tag

            # 3. 기본 프로필 정보 업데이트
            if persona_data.profile_msg is not None:
                persona.profile_msg = persona_data.profile_msg
            if persona_data.profile_image_url is not None:
                persona.profile_image_url = persona_data.profile_image_url

            # 4. 취향 정보(영화, 장르, 인물) 업데이트 - 기존 연결 삭제 후 재삽입
            try:
                with tracer.start_as_current_span("persona.update_preferences"):
                    if persona_data.fav_movie_ids is not None:
                        db.query(FavMovie).filter(FavMovie.persona_id == persona.id).delete()
                        for movie_id in persona_data.fav_movie_ids:
                            db.add(FavMovie(persona_id=persona.id, movie_id=movie_id))
                            
                    if persona_data.fav_genre_ids is not None:
                        db.query(FavGenre).filter(FavGenre.persona_id == persona.id).delete()
                        for genre_id in persona_data.fav_genre_ids:
                            db.add(FavGenre(persona_id=persona.id, genre_id=genre_id))
                            
                    if persona_data.fav_people_ids is not None:
                        db.query(FavPeople).filter(FavPeople.persona_id == persona.id).delete()
                        for people_id in persona_data.fav_people_ids:
                            db.add(FavPeople(persona_id=persona.id, people_id=people_id, type="FAVORITE"))
                            
                    db.flush()
                    db.commit()
                    db.refresh(persona)
                    
                    return persona
                    
            except Exception as e:
                db.rollback()
                span.record_exception(e)
                raise HTTPException(
                    status_code=500,
                    detail={"code": "DATABASE_SAVE_FAILED", "message": f"페르소나 정보 수정 중 오류 발생: {str(e)}"}
                )