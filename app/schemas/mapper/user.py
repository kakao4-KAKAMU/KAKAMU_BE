from datetime import datetime
from typing import Optional

from app.models.user import User as UserModel
from app.schemas.base.user import UserAccount, UserPublic, UserSimple, UserSimpleWithFollow


class UserMapper:
    @staticmethod
    def to_simple(user: UserModel) -> UserSimple:
        return UserSimple(
            id=user.id,
            nickname=user.nickname,
            tag=user.tag,
            profile_image=user.profile_image_url,
            created_at=user.created_at,
        )

    @staticmethod
    def to_simple_or_anonymous(user: Optional[UserModel]) -> UserSimple:
        if not user or user.status == "DELETED":
            return UserSimple(
                id=None,
                nickname="알 수 없음",
                tag="",
                profile_image=None,
                created_at=user.created_at if user else datetime(1970, 1, 1),
            )
        return UserMapper.to_simple(user)

    @staticmethod
    def to_simple_with_follow(user: UserModel, *, is_following: bool = False) -> UserSimpleWithFollow:
        return UserSimpleWithFollow(
            **UserMapper.to_simple(user).model_dump(),
            is_following=is_following,
        )

    @staticmethod
    def to_account(user: UserModel) -> UserAccount:
        return UserAccount(
            **UserMapper.to_simple(user).model_dump(),
            username=user.username,
            profile_msg=user.profile_msg,
            phone=user.phone,
        )

    @staticmethod
    def to_public(
        user: UserModel,
        *,
        is_following: bool = False,
        follower_count: int = 0,
        following_count: int = 0,
        post_count: int = 0,
    ) -> UserPublic:
        return UserPublic(
            **UserMapper.to_simple_with_follow(user, is_following=is_following).model_dump(),
            profile_msg=user.profile_msg,
            follower_count=follower_count,
            following_count=following_count,
            post_count=post_count,
        )
