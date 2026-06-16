from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from uuid import UUID
from app.models import User, Follow, Post
from typing import Optional

class UserService:
    
    @staticmethod
    def get_user(db: Session, user_id: UUID) -> User:
        """특정 유저의 정보를 데이터베이스에서 조회합니다."""
        user = db.scalar(select(User).where(User.id == user_id, User.status == "ACTIVE"))
        
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "요청한 사용자를 찾을 수 없습니다."})
            
        return user

    @staticmethod
    def get_public_user(db: Session, target_user_id: UUID, viewer_user_id: Optional[UUID] = None) -> dict:
        """특정 유저의 공개 프로필 정보(팔로워, 팔로잉, 게시물 수 등 포함)를 반환합니다."""
        user = db.scalar(select(User).where(User.id == target_user_id, User.status == "ACTIVE"))
        
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "요청한 사용자를 찾을 수 없습니다."})
            
        follower_count = db.scalar(select(func.count(Follow.follower_id)).where(Follow.following_id == target_user_id))
        following_count = db.scalar(select(func.count(Follow.following_id)).where(Follow.follower_id == target_user_id))
        post_count = db.scalar(select(func.count(Post.id)).where(Post.user_id == target_user_id, Post.status == "ACTIVE"))
        
        is_following = False
        if viewer_user_id:
            is_following = db.scalar(select(Follow).where(
                and_(Follow.follower_id == viewer_user_id, Follow.following_id == target_user_id)
            )) is not None
            
        return {
            "id": user.id,
            "nickname": user.nickname,
            "tag": user.tag,
            "profile_image_url": user.profile_image_url,
            "profile_msg": user.profile_msg,
            "created_at": user.created_at,
            "is_following": is_following,
            "follower_count": follower_count,
            "following_count": following_count,
            "post_count": post_count
        }

user_service = UserService()