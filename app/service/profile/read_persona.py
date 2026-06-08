from fastapi import HTTPException
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import Session
from app.models import Persona, Block, Follow, Post
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

        personas = list(db.scalars(stmt).all())
        for persona in personas:
            follower_count = db.scalar(select(func.count(Follow.id)).where(Follow.following_id == user_id))
            following_count = db.scalar(select(func.count(Follow.id)).where(Follow.follower_id == user_id))
            post_count = db.scalar(select(func.count(Post.id)).where(Post.persona_id == persona.id, Post.status == "ACTIVE"))
            setattr(persona, "follower_count", follower_count)
            setattr(persona, "following_count", following_count)
            setattr(persona, "post_count", post_count)
            
        return personas

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

        follower_count = db.scalar(select(func.count(Follow.id)).where(Follow.following_id == user_id))
        following_count = db.scalar(select(func.count(Follow.id)).where(Follow.follower_id == user_id))
        post_count = db.scalar(select(func.count(Post.id)).where(Post.persona_id == persona_id, Post.status == "ACTIVE"))
        
        setattr(persona, "follower_count", follower_count)
        setattr(persona, "following_count", following_count)
        setattr(persona, "post_count", post_count)

        return persona

    # 타인의 공개 프로필(페르소나) 조회
    @staticmethod
    async def get_public_persona_profile(
        db: Session,
        target_persona_id: UUID,
        viewer_persona_id: UUID
    ) -> Persona:
        viewer_persona = db.scalar(select(Persona).where(Persona.id == viewer_persona_id))
        target_persona = db.scalar(select(Persona).where(Persona.id == target_persona_id, Persona.status == "ACTIVE"))

        if not viewer_persona or not target_persona:
            raise HTTPException(
                status_code=404,
                detail={"code": "PERSONA_NOT_FOUND", "message": "존재하지 않거나 삭제된 프로필입니다."}
            )

        viewer_user_id = viewer_persona.user_id
        target_user_id = target_persona.user_id

        # 차단 여부 검증: 내가 상대방을 차단했거나, 상대방이 나를 차단했는지 확인 (양방향)
        block_stmt = select(Block).where(
            or_(
                and_(Block.blocker_id == viewer_user_id, Block.blocked_id == target_user_id),
                and_(Block.blocker_id == target_user_id, Block.blocked_id == viewer_user_id)
            )
        )
        is_blocked = db.scalar(block_stmt) is not None

        if is_blocked:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN_BLOCKED_USER", "message": "차단한 사용자의 프로필은 볼 수 없습니다."}
            )

        # 팔로우 여부 확인
        follow_stmt = select(Follow).where(
            Follow.follower_id == viewer_user_id,
            Follow.following_id == target_user_id
        )
        is_following = db.scalar(follow_stmt) is not None
        setattr(target_persona, "is_following", is_following)

        follower_count = db.scalar(select(func.count(Follow.id)).where(Follow.following_id == target_user_id))
        following_count = db.scalar(select(func.count(Follow.id)).where(Follow.follower_id == target_user_id))
        post_count = db.scalar(select(func.count(Post.id)).where(Post.persona_id == target_persona_id, Post.status == "ACTIVE"))
        
        setattr(target_persona, "follower_count", follower_count)
        setattr(target_persona, "following_count", following_count)
        setattr(target_persona, "post_count", post_count)
        
        return target_persona
