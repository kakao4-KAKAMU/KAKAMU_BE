from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from uuid import UUID
from app.models import User, Follow, Post
from typing import Optional, List, Dict
from app.schemas.mapper.user import UserMapper
from app.schemas.response.user import UserPublicResponse

class UserReadService:
    @staticmethod
    def get_user_follow_status_by_user_ids(db: Session, user_id: List[UUID], target_user_ids: UUID) -> Dict[UUID, bool]:
        return db.query(Follow).filter(Follow.follower_id == user_id, Follow.following_id == target_user_ids).all()

    @staticmethod
    def get_user_info_by_ids(db: Session, user_ids: List[UUID]) -> Dict[UUID, User]:
        return db.query(User).filter(User.id.in_(user_ids)).all()