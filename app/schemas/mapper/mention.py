from app.models.user import User as UserModel
from app.schemas.base.mention import Mention


class MentionMapper:
    @staticmethod
    def to_mention(user: UserModel) -> Mention:
        return Mention(id=user.id, nickname=user.nickname, tag=user.tag)

    @staticmethod
    def from_row(user_id, nickname: str, tag: str) -> Mention:
        return Mention(id=user_id, nickname=nickname, tag=tag)
