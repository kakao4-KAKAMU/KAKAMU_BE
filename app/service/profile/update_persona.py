import redis

import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, update
from sqlalchemy.orm import Session
from app.models.models import Persona
from app.schemas.profile import PersonaEdit
from app.service.profile.read_persona import PersonaReadService

class PersonaUpdateService:

    # 특정 페르소나 수정
    @staticmethod
    async def update_persona(db: Session,redis_client, persona_id: int, edit_data: PersonaEdit, user_id: int) -> Persona:
        db_persona = db.get(Persona, persona_id) # persona_id로 Persona 테이블 찾음


        if not db_persona:
            raise HTTPException(status_code=404, detail="존재하지 않는 페르소나 입니다.")
        if db_persona.user_id != user_id:
            raise HTTPException(status_code=403, detail="이 페르소나를 수정할 권한이 없습니다.")

        # 사용자가 실제로 보낸 값만 딕셔너리로 추출 (exclude_unset=True)
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
            # 페르소나 기간 연장 로직 호출
            await PersonaReadService.get_current_active_persona_id(
                db = db,
                redis_client = redis_client,
                user_id = user_id
            )

            return db_persona
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"데이터베이스 저장 중 오류 발생 {str(e)}")

    # 특정 페르소나 활성화 (전환)
    @staticmethod
    async def activate_persona(
            db: Session,
            redis_client,
            user_id: int,
            persona_id: int
    ) -> Persona:
        redis_key = f"kakamu:user:{user_id}:current_persona"
        THREE_DAY = 259200

        target_stmt = select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == user_id,
            Persona.status == "ACTIVE"
        )

        target_persona = db.scalar(target_stmt)

        if not target_persona:
            raise HTTPException(
                status_code=404,
                detail="활성화할 페르소나를 찾을 수 없습니다."
            )

        try:
            # 해당 유저의 기존 활성 페르소나 전부 off
            db.execute(
                update(Persona)
                .where(
                    Persona.user_id == user_id,
                    Persona.status == "ACTIVE"
                )
                .values(preference_status="off")
            )

            # 선택한 페르소나만 on
            target_persona.preference_status = "on"

            db.commit()
            db.refresh(target_persona)

            # Redis 현재 페르소나도 갱신
            await redis_client.set(redis_key, target_persona.id, ex=THREE_DAY)

            return target_persona

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"페르소나 활성화 중 오류 발생: {str(e)}"
            )