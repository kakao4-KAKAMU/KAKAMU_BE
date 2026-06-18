from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User, Follow, Block
from app.schemas.response.relation import RelationResponse
from uuid import UUID

class RelationService:
    async def follow(self, db: Session, follower_id: UUID, following_id: UUID) -> RelationResponse:
        target = db.query(User).filter(User.id == following_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="팔로우 대상 유저를 찾을 수 없습니다.")

        # 차단 여부 검증 (어느 한쪽이라도 차단했으면 팔로우 불가 처리)
        is_blocked = db.query(Block).filter(
            ((Block.blocker_id == follower_id) & (Block.blocked_id == following_id)) |
            ((Block.blocker_id == following_id) & (Block.blocked_id == follower_id))
        ).first()
        
        if is_blocked:
            raise HTTPException(status_code=403, detail="차단된 상태이므로 팔로우할 수 없습니다.")
        
        existing = db.query(Follow).filter_by(follower_id=follower_id, following_id=following_id).first()
        if existing:
            return RelationResponse(status="success", message="이미 팔로우 중입니다.")

        new_follow = Follow(follower_id=follower_id, following_id=following_id)
        db.add(new_follow)
        db.commit()
        return RelationResponse(status="success", message="팔로우가 완료되었습니다.")

    async def unfollow(self, db: Session, follower_id: UUID, following_id: UUID) -> RelationResponse:
        existing = db.query(Follow).filter_by(follower_id=follower_id, following_id=following_id).first()
        if not existing:
            return RelationResponse(status="success", message="팔로우 상태가 아닙니다.")

        db.delete(existing)
        db.commit()
        return RelationResponse(status="success", message="언팔로우 되었습니다.")

    async def block(self, db: Session, blocker_id: UUID, blocked_id: UUID, level: str) -> RelationResponse:
        target = db.query(User).filter(User.id == blocked_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="차단 대상 유저를 찾을 수 없습니다.")

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
        return RelationResponse(status="success", message="차단이 완료되었습니다.")

    async def unblock(self, db: Session, blocker_id: UUID, blocked_id: UUID) -> RelationResponse:
        existing = db.query(Block).filter_by(blocker_id=blocker_id, blocked_id=blocked_id).first()
        if not existing:
            return RelationResponse(status="success", message="차단된 상태가 아닙니다.")

        db.delete(existing)
        db.commit()
        return RelationResponse(status="success", message="차단이 해제되었습니다.")

relation_service = RelationService()