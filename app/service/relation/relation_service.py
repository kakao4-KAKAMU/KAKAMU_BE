from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Persona, Follow, Block
from uuid import UUID

class RelationService:
    async def follow(self, db: Session, follower_id: UUID, following_id: UUID):
        target = db.query(Persona).filter(Persona.id == following_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="팔로우 대상 페르소나를 찾을 수 없습니다.")

        # 차단 여부 검증 (어느 한쪽이라도 차단했으면 팔로우 불가 처리)
        is_blocked = db.query(Block).filter(
            ((Block.blocker_id == follower_id) & (Block.blocked_id == following_id)) |
            ((Block.blocker_id == following_id) & (Block.blocked_id == follower_id))
        ).first()
        
        if is_blocked:
            raise HTTPException(status_code=403, detail="차단된 상태이므로 팔로우할 수 없습니다.")
        
        existing = db.query(Follow).filter_by(follower_id=follower_id, following_id=following_id).first()
        if existing:
            return {"status": "success", "message": "이미 팔로우 중입니다."}

        new_follow = Follow(follower_id=follower_id, following_id=following_id)
        db.add(new_follow)
        db.commit()
        return {"status": "success", "message": "팔로우가 완료되었습니다."}

    async def unfollow(self, db: Session, follower_id: UUID, following_id: UUID):
        existing = db.query(Follow).filter_by(follower_id=follower_id, following_id=following_id).first()
        if not existing:
            return {"status": "success", "message": "팔로우 상태가 아닙니다."}
        
        db.delete(existing)
        db.commit()
        return {"status": "success", "message": "언팔로우 되었습니다."}

    async def block(self, db: Session, blocker_id: UUID, blocked_id: UUID, level: str):
        target = db.query(Persona).filter(Persona.id == blocked_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="차단 대상 페르소나를 찾을 수 없습니다.")

        # 차단 시 기존의 팔로우 관계가 존재한다면 양방향 모두 확인하여 강제 연결 해제
        db.query(Follow).filter(
            ((Follow.follower_id == blocker_id) & (Follow.following_id == blocked_id)) |
            ((Follow.follower_id == blocked_id) & (Follow.following_id == blocker_id))
        ).delete(synchronize_session=False)

        existing_block = db.query(Block).filter_by(blocker_id=blocker_id, blocked_id=blocked_id).first()
        if existing_block:
            existing_block.level = level
        else:
            new_block = Block(blocker_id=blocker_id, blocked_id=blocked_id, level=level)
            db.add(new_block)
        
        db.commit()
        # USER 차단 시, 피드 조회나 검색 쿼리단에서 Block level='USER'일 때 target의 user_id를 참조해 전체 차단으로 적용하면 익명성을 유지할 수 있습니다.
        return {"status": "success", "message": "차단이 완료되었습니다."}

    async def unblock(self, db: Session, blocker_id: UUID, blocked_id: UUID):
        existing = db.query(Block).filter_by(blocker_id=blocker_id, blocked_id=blocked_id).first()
        if not existing:
            return {"status": "success", "message": "차단된 상태가 아닙니다."}
        
        db.delete(existing)
        db.commit()
        return {"status": "success", "message": "차단이 해제되었습니다."}

relation_service = RelationService()