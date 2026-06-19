from app.schemas.base.common import SuccessMessageResponse, SuccessResponse

__all__ = ["SuccessResponse", "SuccessMessageResponse", "IdResponse", "PostIdResponse", "CommentIdResponse"]


class IdResponse(SuccessResponse):
    id: int


class PostIdResponse(SuccessResponse):
    post_id: int


class CommentIdResponse(SuccessResponse):
    comment_id: int
