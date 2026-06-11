from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import Persona, Post, Comment
from uuid import UUID

class PersonaDeleteService:


    @staticmethod
    async def delete_persona(
            db: Session,
            user_id: UUID,
            persona_id: UUID
    ):

        stmt = select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == user_id,
            Persona.status == "ACTIVE"
        )

        persona = db.scalar(stmt)

        if not persona:
            raise HTTPException(
                status_code=404,
                detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없습니다."}
            )

        # 남은 활성 페르소나 개수 확인 (최소 1개는 유지)
        count_stmt = select(func.count(Persona.id)).where(
            Persona.user_id == user_id,
            Persona.status == "ACTIVE"
        )
        active_persona_count = db.scalar(count_stmt)

        if active_persona_count <= 1:
            raise HTTPException(
                status_code=400,
                detail={"code": "MINIMUM_PERSONA_REQUIRED", "message": "최소 1개의 페르소나는 유지해야 하므로 삭제할 수 없습니다."}
            )

        try:
            # 1. 페르소나가 작성한 게시물 및 댓글 비활성화 (INACTIVE)
            # (Persona 삭제 시 DB 레벨에서 ondelete="SET NULL"이 발생하므로 삭제 전 상태 업데이트 필요)
            db.query(Post).filter(Post.persona_id == persona_id).update({"status": "INACTIVE"}, synchronize_session=False)
            db.query(Comment).filter(Comment.persona_id == persona_id).update({"status": "INACTIVE"}, synchronize_session=False)

            # 2. 페르소나 영구 삭제 (Hard Delete)
            db.delete(persona)
            db.commit()

        except Exception as e:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail={"code": "PERSONA_DELETE_FAILED", "message": f"페르소나 삭제 중 오류 발생 : {str(e)}"}
            )

        return None