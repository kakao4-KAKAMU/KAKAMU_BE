from pydantic import BaseModel, Field
from typing import List, Optional

class PostUpdate(BaseModel):
    """게시물 수정 시 전달받는 데이터 (수정할 필드만 선택적 포함 가능)"""
    title: Optional[str] = Field(None, max_length=255, description="수정할 게시물 제목")
    content: Optional[str] = Field(None, description="수정할 게시물 본문")
    movie_ids: Optional[List[int]] = Field(None, min_length=1, description="수정할 공식 영화 ID 목록")
    image_urls: Optional[List[str]] = Field(None, max_length=5, description="수정할 첨부 이미지 URL 목록")
    is_spoiler: Optional[int] = Field(None, ge=0, le=1, description="스포일러 여부 (0: 일반, 1: 스포일러)")