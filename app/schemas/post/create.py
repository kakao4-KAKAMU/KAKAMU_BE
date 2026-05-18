from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class PostCreate(BaseModel):
    title: str = Field(..., max_length=255, description="게시물 제목")
    content: str = Field(..., description="게시물 본문")
    # 영화 태깅 최소 1개 필수 정책 적용
    movie_ids: List[int] = Field(..., min_length=1, description="태깅된 공식 영화 ID 목록 (최소 1개)")
    # 최대 5장 이미지 제한 정책 적용
    image_urls: Optional[List[str]] = Field(default=[], max_length=5, description="첨부 이미지 URL 목록 (최대 5장)")
    is_spoiler: int = Field(default=0, ge=0, le=1, description="스포일러 여부 (0: 일반, 1: 스포일러)")

    @field_validator('title', 'content')
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("공백으로만 이루어질 수 없습니다.")
        return v
        
    @field_validator('image_urls')
    @classmethod
    def check_urls(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError("유효한 HTTP/HTTPS URL이어야 합니다.")
        return v
