import re,string,random
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models import Persona
from app.schemas.profile import PersonaEdit
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

class PersonaUpdateService:

    # 태그 랜덤 생성 함수
    @staticmethod
    def generate_random_tag(length: int = 5) -> str:
        characters = string.ascii_lowercase + string.digits  # 소문자와 숫자 조합
        return ''.join(random.choices(characters, k=length))  # 길이는 5글자

    # 특정 페르소나 수정
    @staticmethod
    async def update_persona(db: Session, persona_id: UUID, edit_data: PersonaEdit, user_id: UUID) -> Persona:
        with tracer.start_as_current_span("persona.update") as span:
            span.set_attribute("persona.id", str(persona_id))
            span.set_attribute("user.id", str(user_id))

            MAX_RETRY = 10
            db_persona = db.get(Persona, persona_id) # persona_id로 Persona 테이블 찾음

            if not db_persona:
                span.set_attribute("persona.update.result", "failed")
                span.set_attribute("persona.update.fail_reason", "persona_not_found")
                raise HTTPException(status_code=404, detail="존재하지 않는 페르소나 입니다.")

            if db_persona.user_id != user_id:
                span.set_attribute("persona.update.result", "failed")
                span.set_attribute("persona.update.fail_reason", "forbidden")
                raise HTTPException(status_code=403, detail="이 페르소나를 수정할 권한이 없습니다.")

            with tracer.start_as_current_span("persona.update.extract_update_data") as update_data_span:
                # 사용자가 실제로 보낸 값만 딕셔너리로 추출 (exclude_unset=True)
                update_data = edit_data.model_dump(exclude_unset=True)
                update_data_span.set_attribute("update.field_count", len(update_data))
                update_data_span.set_attribute("update.has_nickname", "nickname" in update_data)

            # 닉네임이 포함될 시 검사 로직
            if "nickname" in update_data and update_data["nickname"] is not None:
                new_nickname = update_data["nickname"]

                if db_persona.nickname == new_nickname:
                    span.set_attribute("persona.update.result", "failed")
                    span.set_attribute("persona.update.fail_reason", "same_nickname")
                    raise HTTPException(
                        status_code=400,
                        detail="현재 닉네임과 동일합니다."
                    )

                tag=None

                with tracer.start_as_current_span("persona.update.generate_unique_tag") as tag_span:
                    for retry_count in range(MAX_RETRY):  # 10번 태그 생성 시도
                        candidate_tag = PersonaUpdateService.generate_random_tag()  # 랜덤 태그 생성

                        exist_stmt = select(Persona).where(
                            and_(
                                Persona.nickname == new_nickname,  # and 연산으로 name, tag 비교
                                Persona.tag == candidate_tag
                            )
                        )

                        existing_persona = db.scalar(exist_stmt)  # 닉네임 + 태그로 중복 검사

                        if not existing_persona:  # 만약 없으면
                            tag = candidate_tag  # 태그를 생성된 태그로 지정하고
                            tag_span.set_attribute("tag.retry_count", retry_count + 1)
                            break  # 반복문 종료

                db_persona.nickname = new_nickname
                db_persona.tag = tag

                # 처리했으니깐 삭제
                del update_data["nickname"]

            # 나머지 일괄 처리
            try:
                with tracer.start_as_current_span("persona.update.apply_fields"):
                    for key, value in update_data.items():
                        setattr(db_persona, key, value)

                with tracer.start_as_current_span("persona.update.db_commit"):
                    db.commit()
                with tracer.start_as_current_span("persona.update.db_refresh"):
                    db.refresh(db_persona)

                span.set_attribute("persona.update.result", "success")

                return db_persona
            except Exception as e:
                db.rollback()

                span.record_exception(e)
                span.set_attribute("persona.update.result", "failed")
                span.set_attribute("persona.update.fail_reason", "database_error")

                raise HTTPException(status_code=500, detail=f"데이터베이스 저장 중 오류 발생 {str(e)}")
