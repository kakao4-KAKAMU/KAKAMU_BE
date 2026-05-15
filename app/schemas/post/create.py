from pydantic import BaseModel, Field
from typing import List, Optional

class PostCreate(BaseModel):
    title: str = Field(..., max_length=255, description="게시물 제목")
    content: str = Field(..., description="게시물 본문")
    # 영화 태깅 최소 1개 필수 정책 적용
    movie_ids: List[int] = Field(..., min_length=1, description="태깅된 공식 영화 ID 목록 (최소 1개)")
    # 최대 5장 이미지 제한 정책 적용
    image_urls: Optional[List[str]] = Field(default=[], max_length=5, description="첨부 이미지 URL 목록 (최대 5장)")
    is_spoiler: int = Field(default=0, description="스포일러 여부 (0: 일반, 1: 스포일러)")
