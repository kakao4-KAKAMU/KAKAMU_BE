from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List

class SuccessResponse(BaseModel):
    status: str = Field(default="success", description="응답 상태")
    message: Optional[str] = Field(default=None, description="성공 메시지 (선택)")

class SuccessMessageResponse(BaseModel):
    message: str = Field(..., description="성공 메시지")

class IdResponse(SuccessResponse):
    id: int = Field(..., description="생성/수정된 리소스의 ID")

class PostIdResponse(SuccessResponse):
    post_id: int = Field(..., description="게시물 ID")

class CommentIdResponse(SuccessResponse):
    comment_id: int = Field(..., description="댓글 ID")