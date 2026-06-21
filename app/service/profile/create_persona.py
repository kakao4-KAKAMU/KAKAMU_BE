from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Persona
from app.models import FavMovie, FavGenre, FavPeople
from app.schemas.base.persona import Persona as PersonaSchema
from app.schemas.mapper.persona import PersonaMapper
from app.schemas.request.profile import PersonaCreate
from app.service.profile.ml_sync import persona_ml_sync_service
from opentelemetry import trace


tracer = trace.get_tracer(__name__)


class PersonaCreateService:

    @staticmethod
    async def create_new_persona(
            db: Session,
            persona_data: PersonaCreate,
            user_id: UUID
    ) -> PersonaSchema:



        with tracer.start_as_current_span("persona.create") as span:
            span.set_attribute("user_id", str(user_id))

            name = persona_data.nickname

            if not name:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "MISSING_NICKNAME", "message": "닉네임을 입력해주세요"}
                )
                
            with tracer.start_as_current_span("persona.check_duplicate_nickname"):
                # 본인이 이미 같은 닉네임의 페르소나를 가지고 있는지 검사
                duplicate_stmt = select(Persona).where(Persona.user_id == user_id, Persona.nickname == name, Persona.status != "DELETED")
                if db.scalar(duplicate_stmt):
                    span.set_attribute("error.reason", "duplicate_persona_nickname")
                    raise HTTPException(
                        status_code=400,
                        detail={"code": "DUPLICATE_PERSONA_NICKNAME", "message": "이미 사용 중인 페르소나 닉네임입니다."}
                    )

            with tracer.start_as_current_span("persona.count_user_personas") as count_span:
                # 페르소나 계정이 있는 지 검사
                count_stmt = select(func.count(Persona.id)).where(Persona.user_id == user_id)
                persona_count = db.scalar(count_stmt)  # 페르소나 계정 개수 반환

                count_span.set_attribute("persona.count", persona_count)

            if persona_count >= 5:  # 계정이 5개 이상이면 생성 금지
                span.set_attribute("error.reason", "persona_limit_exceeded")
                raise HTTPException(
                    status_code=400,
                    detail={"code": "PERSONA_LIMIT_EXCEEDED", "message": "페르소나 계정은 최대 5개 생성 가능합니다."}
                )

            try:
                profile_image_url = (
                    persona_data.profile_image_url
                    if persona_data.profile_image_url
                    else "/static/default_profile_image.png"
                )
                new_profile = Persona(
                    user_id=user_id,
                    nickname=name,
                    profile_image_url=profile_image_url,
                    status="ACTIVE",
                    deleted_at=None
                )
                with tracer.start_as_current_span("persona.db_insert_profile"):
                    db.add(new_profile)
                    db.flush() # 페르소나 id 생성

                with tracer.start_as_current_span("persona.db_insert_preferences") as pref_span:
                    fav_movie_count = len(persona_data.fav_movie_ids or [])
                    fav_genre_count = len(persona_data.fav_genre_ids or [])
                    fav_people_count = len(persona_data.fav_people_ids or [])

                    pref_span.set_attribute("fav_movie_count", fav_movie_count)
                    pref_span.set_attribute("fav_genre_count", fav_genre_count)
                    pref_span.set_attribute("fav_people_count", fav_people_count)
                    # 선호 취향(영화, 장르, 인물) 데이터가 넘어왔다면 DB에 저장
                    if persona_data.fav_movie_ids:
                        for movie_id in persona_data.fav_movie_ids: # 리스트 형식
                            db.add(FavMovie(persona_id=new_profile.id, movie_id=movie_id))

                    if persona_data.fav_genre_ids:
                        for genre_id in persona_data.fav_genre_ids:
                            db.add(FavGenre(persona_id=new_profile.id, genre_id=genre_id))

                    if persona_data.fav_people_ids:
                        for people_id in persona_data.fav_people_ids:
                            # 인물의 type("ACTOR", "DIRECTOR" 등)이 필요하지만 우선 "FAVORITE"으로 통일하여 저장
                            db.add(FavPeople(persona_id=new_profile.id, people_id=people_id, type="FAVORITE"))

                    if persona_data.fav_movie_ids or persona_data.fav_genre_ids or persona_data.fav_people_ids:
                        db.flush()
                with tracer.start_as_current_span("persona.db_commit"):
                    db.commit()
                with tracer.start_as_current_span("persona.db_refresh"):
                    db.refresh(new_profile)

                await persona_ml_sync_service.sync_create(db, new_profile, persona_data)

                return PersonaMapper.to_persona(new_profile)
            except IntegrityError as e:
                db.rollback()
                span.record_exception(e)
                span.set_attribute("error.reason", "invalid_reference_data")
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_REFERENCE_DATA", "message": "존재하지 않는 영화, 장르 또는 인물 ID가 포함되어 있습니다."}
                )
            except Exception as e:
                db.rollback()
                span.record_exception(e)
                span.set_attribute("error.reason", "database_save_failed")
                raise HTTPException(status_code=500, detail={"code": "DATABASE_SAVE_FAILED", "message": f"데이터베이스 저장 중 오류 발생 {str(e)}"})