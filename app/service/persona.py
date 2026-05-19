from app.core.redis import redis_client
import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models.models import Persona
from app.schemas.profile import PersonaCreate, PersonaEdit

class PersonaService:
    def __init__(self):
        self.redis = redis_client

    @staticmethod
    def create_new_persona(db: Session, persona_data: PersonaCreate, user_id: int) -> Persona:
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
        exist_stmt = select(Persona).where(
            and_(
                Persona.nickname == name,  # and 연산으로 name, tag 비교
                Persona.tag == tag
            )
        )

        existing_persona = db.scalar(exist_stmt)  # 존재하는지 확인, scalar는 없으면 None 반환

        if existing_persona:
            raise HTTPException(
                status_code=400,  # 중복된 닉네임있으면 400 에러 발생
                detail=f"이미 존재하는 닉네임과 태그 조합입니다.({persona_data.nickname})"
            )

        # 페르소나 계정이 있는 지 검사
        count_stmt = select(func.count(Persona.id)).where(Persona.user_id == user.id)
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
            new_profile = Persona(
                user_id=user_id,
                nickname=name,
                profile_msg=persona_data.profile_msg,
                persona_type=persona_data.persona_type,
                is_main=is_main_value,
                preference_status="on",  # 현재 활성화된 페르소나 프로필 (on, off)
                tag=tag,
                proflie_image_url=persona_data.proflie_image_url,
                status="ACTIVE",
                delete_at=None
            )

            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)

            return new_profile  # schemas/profile.py에 정의한
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"데이터베이스 저장 중 오류 발생")

    # 페르소나 수정
    @staticmethod
    def update_persona(db: Session, edit_data: PersonaEdit, user_id: int) -> Persona:
        db_persona = db.get(Persona,user_id)

        if not db_persona:
            raise HTTPException(status_code = 404, detail = "존재하지 않는 페르소나 입니다.")
        if db_persona.user_id != user_id:
            raise HTTPException(status_code = 403, detail = "이 페르소나를 수정할 권한이 없습니다.")

        update_data = edit_data.model_dump(exclude_unset=True)

        # 닉네임이 포함될 시 검사 로직
        if "nickname" in update_data and update_data["nickname"] is not None:
            new_nickname = update_data["nickname"]
            if '#' not in new_nickname:
                raise HTTPException(
                    status_code=400,
                    detail="닉네임 형식이 틀립니다. '닉네임#태그' 형태로 입력하세요. "
                )

            name, tag = new_nickname.split('#', 1)
            # 태그 형식 검사
            if not re.fullmatch(r'[A-Za-z0-9]{3,5}', tag):  # 대소문자, 0~9, 3글자에서 5글자
                raise HTTPException(
                    status_code=400,
                    detail="태그 형식이 틀립니다. 태그는 숫자와 영어만 가능하며 3~5글자여야 합니다."
                )
            # 중복 검사
            exist_stmt = select(Persona).where(
                and_(
                    Persona.nickname == name,  # and 연산으로 name, tag 비교
                    Persona.tag == tag
                )
            )

            existing_persona = db.scalar(exist_stmt)  # 존재하는지 확인, scalar는 없으면 None 반환

            if existing_persona:
                raise HTTPException(
                    status_code=400,  # 중복된 닉네임있으면 400 에러 발생
                    detail=f"이미 존재하는 닉네임과 태그 조합입니다."
                )

            db_persona.nickname = name
            db_persona.tag = tag

            # 처리했으니깐 삭제
            del update_data["nickname"]

        # 나머지 일괄 처리
        try:
            for key, value in update_data.items():
                setattr(db_persona, key, value)

            db.commit()
            db.refresh(db_persona)
            return db_persona
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code = 500, detail=f"데이터베이스 저장 중 오류 발생")

    # 특정 페르소나를 활성화
    async def activate_persona(self,db: Session,persona_id: id, user_id: int):
        db_persona = db.get(Persona,persona_id)
        THREE_DAY = 259200 # 3일 동안 활성화
        if not db_persona or db_persona.user_id != user_id:
            return False

        try: # 해당 유저의 모든 페르소나를 off로 전환하고
            db.execute(
                update(Persona).where(Persona.id == persona_id).values(preference_status="off")
            )
            db_persona.preference_status = "on" # 선택한 페르소나만 on으로 전환
            db.commit()

            redis_key = f"kakamu:user:{user_id}:current_persona"

            await self.redis.set(redis_key,persona_id, ex=THREE_DAY) # 3일동안 유지

        except Exception as e:
            db.rollback()
            return False

    # 현재 활성화 된 계정 가져오기 + 자동 기간 갱신
    @staticmethod
    async def get_current_active_persona_id(self,db: Session, user_id: int) -> int:
        redis_key = f"kakamu:user:{user_id}:current_persona"
        THREE_DAY = 259200

        # redis에 값이 있는지 확인
        cached_persona_id = await self.redis.get(redis_key)

        # redis에 값이 존재하면 만료 시간 3일 연장
        if cached_persona_id is not None:
            await self.redis.expire(redis_key, THREE_DAY)
            return int(cached_persona_id)

        # 만약 없으면 현재 "on" 상태의 페르소나 조회
        stmt = select(Persona).where(
            Persona.user_id == user_id,
            Persona.preference_status == "on"
        )

        active_id = db.scalar(stmt)

        # 그 페르소나로 다시 redis에 등록
        if active_id:
            await self.redis.expire(redis_key,active_id, ex=THREE_DAY)
            return active_id

        return None



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