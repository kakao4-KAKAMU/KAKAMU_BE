from pydantic import BaseModel, Field
from typing import Optional

class CommentCreate(BaseModel):
    content: str = Field(..., max_length=1000, description="댓글 본문")
    parent_id: Optional[int] = Field(default=None, description="대댓글인 경우 부모 댓글의 ID")
    is_spoiler: int = Field(default=0, description="스포일러 여부 (0: 일반, 1: 스포일러)")
