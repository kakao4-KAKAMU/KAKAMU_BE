from pydantic import BaseModel, Field

class LikeToggleRequest(BaseModel):
    target_type: str = Field(..., description="POST 또는 COMMENT")
    target_id: int = Field(..., description="대상 게시물/댓글 ID")