from fastapi import HTTPException
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
from app.models import Persona, EntityRelationshipLog, Follow
from typing import List
from uuid import UUID

class PersonaReadService:

    # 내 모든 페르소나 조회
    @staticmethod
    async def get_my_personas(db: Session, user_id: UUID) -> List[Persona]:
        stmt = select(Persona).where(
            Persona.user_id == user_id,
            Persona.status != "DELETED"
        )

        return list(db.scalars(stmt).all())

    # 특정 페르소나 조회
    @staticmethod
    async def get_persona_detail(
        db: Session,
        user_id: UUID,
        persona_id: UUID
    ) -> Persona:
        stmt = select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == user_id,
            Persona.status != "DELETED"
        )

        persona = db.scalar(stmt)

        if not persona:
            raise HTTPException(
                status_code=404,
                detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없습니다."}
            )

        return persona

    # 타인의 공개 프로필(페르소나) 조회
    @staticmethod
    async def get_public_persona_profile(
        db: Session,
        target_persona_id: UUID,
        viewer_persona_id: UUID
    ) -> Persona:
        
        # 차단 여부 검증: 내가 상대방을 차단했거나, 상대방이 나를 차단했는지 확인 (양방향)
        block_stmt = select(EntityRelationshipLog).where(
            EntityRelationshipLog.relation_type == "BLOCK",
            or_(
                and_(EntityRelationshipLog.persona_id == viewer_persona_id,
                     EntityRelationshipLog.target_id == target_persona_id),
                and_(EntityRelationshipLog.persona_id == target_persona_id,
                     EntityRelationshipLog.target_id == viewer_persona_id)
            )
        )
        is_blocked = db.scalar(block_stmt)

        if is_blocked:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN_BLOCKED_USER", "message": "차단한 사용자의 프로필은 볼 수 없습니다."}
            )

        stmt = select(Persona).where(
            Persona.id == target_persona_id,
            Persona.status == "ACTIVE"  # 다른 사람의 프로필은 활성 상태일 때만 조회
        )

        persona = db.scalar(stmt)

        if not persona:
            raise HTTPException(
                status_code=404,
                detail={"code": "PERSONA_NOT_FOUND", "message": "존재하지 않거나 삭제된 프로필입니다."}
            )

        # 팔로우 여부 확인
        follow_stmt = select(Follow).where(
            Follow.follower_id == viewer_persona_id,
            Follow.following_id == target_persona_id
        )
        is_following = db.scalar(follow_stmt) is not None
        setattr(persona, "is_following", is_following)
        
        return persona
