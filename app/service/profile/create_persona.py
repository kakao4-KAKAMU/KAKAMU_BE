import re
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models import Persona
from app.models import FavMovie, FavGenre, FavPeople
from app.schemas.profile import PersonaCreate

class PersonaCreateService:
    @staticmethod
    async def create_new_persona(db: Session, persona_data: PersonaCreate, user_id: UUID) -> Persona:
        DEFAULT_PROFILE_IMAGE_URL = "/static/default_profile_image.png"
        # 닉네임 형식 검사 : 닉네임#태그
        if '#' not in persona_data.nickname:
            raise HTTPException(
                status_code=400,
                detail="닉네임 형식이 틀립니다. '닉네임#태그' 형태로 입력하세요. "
            )

        name, tag = persona_data.nickname.split('#', 1)
        # 태그 형식 검사
        if not re.fullmatch(r'[A-Za-z0-9]{3,5}', tag):  # 대소문자, 0~9, 3글자에서 5글자
            raise HTTPException(
                status_code=400,
                detail="태그 형식이 틀립니다. 태그는 숫자와 영어만 가능하며 3~5글자여야 합니다."
            )
        # persona 테이블에서 닉네임이 존재하는 지 검사
        # select(Persona) = select * from Persona;
        # 지금 이 상태는 sql 문 실행한 것이 아님, 실행 계획
        exist_stmt = select(Persona).where(
            and_(
                Persona.nickname == name,  # and 연산으로 name, tag 비교
                Persona.tag == tag
            )
        )

        # 여기서 실제 sql 문 실행 존재하면 Persona 객체 반환
        existing_persona = db.scalar(exist_stmt)

        # 존재하면 중복된 닉네임이 있으니깐 400 에러  발생
        if existing_persona:
            raise HTTPException(
                status_code=400,
                detail=f"이미 존재하는 닉네임과 태그 조합입니다.({persona_data.nickname})"
            )

        # 페르소나 계정이 있는 지 검사
        count_stmt = select(func.count(Persona.id)).where(Persona.user_id == user_id)
        persona_count = db.scalar(count_stmt)  # 페르소나 계정 개수 반환

        if persona_count >= 5:  # 계정이 5개 이상이면 생성 금지
            raise HTTPException(
                status_code=400,
                detail=f"페르소나 계정은 최대 5개 생성 가능합니다."
            )
        elif persona_count == 0:  # 계정이 0개면 메인 계정으로 설정
            is_main_value = 1
        else:
            is_main_value = 0

        try:
            # 기존 페르소나를 비활성화하고 현재 생성중인 페르소나만 활성화
            db.execute(
                update(Persona)
                .where(and_(Persona.user_id == user_id, Persona.status != "DELETED"))
                .values(preference_status="off")
            )
            profile_image_url = persona_data.profile_image_url or DEFAULT_PROFILE_IMAGE_URL
            new_profile = Persona(
                user_id=user_id,
                nickname=name,
                profile_msg=persona_data.profile_msg,
                persona_type=persona_data.persona_type,
                is_main=is_main_value,
                preference_status="on",  # 현재 활성화된 페르소나 프로필 (on, off)
                tag=tag,
                profile_image_url=profile_image_url,
                status="ACTIVE",
                deleted_at=None
            )

            db.add(new_profile)
            db.flush() # 페르소나 id 생성

            # 선호 취향(영화, 장르, 인물) 데이터가 넘어왔다면 DB에 저장
            if persona_data.fav_movie_ids:
                for movie_id in persona_data.fav_movie_ids:
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

            db.commit()
            db.refresh(new_profile)

            return new_profile  # schemas/profile.py에 정의한
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"데이터베이스 저장 중 오류 발생 {str(e)}")
