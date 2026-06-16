from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.models import User, Follow, Post
from typing import Optional
from app.schemas.response.user import UserPublicResponse

class UserService:
    
    @staticmethod
    def get_user(db: Session, user_id: UUID) -> User:
        """특정 유저의 정보를 데이터베이스에서 조회합니다."""
        user = db.query(User).filter(User.id == user_id, User.status == "ACTIVE").first()
        
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "요청한 사용자를 찾을 수 없습니다."})
            
        return user

    @staticmethod
    def get_public_user(
        db: Session,
        target_user_id: UUID,
        viewer_user_id: Optional[UUID] = None,
    ) -> UserPublicResponse:
        """특정 유저의 공개 프로필 정보(팔로워, 팔로잉, 게시물 수 등 포함)를 반환합니다."""
        user = db.query(User).filter(User.id == target_user_id, User.status == "ACTIVE").first()
        
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "요청한 사용자를 찾을 수 없습니다."})
            
        follower_count = db.query(Follow).filter(Follow.following_id == target_user_id).count()
        following_count = db.query(Follow).filter(Follow.follower_id == target_user_id).count()
        post_count = db.query(Post).filter(Post.user_id == target_user_id, Post.status == "ACTIVE").count()
        
        is_following = False
        if viewer_user_id:
            is_following = db.query(Follow).filter(
                Follow.follower_id == viewer_user_id,
                Follow.following_id == target_user_id
            ).first() is not None
            
        return UserPublicResponse(
            id=user.id,
            nickname=user.nickname,
            tag=user.tag,
            profile_image_url=user.profile_image_url,
            profile_msg=user.profile_msg,
            created_at=user.created_at,
            is_following=is_following,
            follower_count=follower_count,
            following_count=following_count,
            post_count=post_count,
        )

user_service = UserService()