from pydantic import BaseModel, Field, field_validator
from app.schemas.request.common import NotEmptyStr, OptionalNotEmptyStr
from typing import List, Optional, Literal

class PostCreate(BaseModel):
    title: NotEmptyStr = Field(..., max_length=255, description="게시물 제목")
    content: NotEmptyStr = Field(..., description="게시물 본문")
    # 영화 태깅 최소 1개 필수 정책 적용
    movie_ids: List[int] = Field(..., min_length=1, description="태깅된 공식 영화 ID 목록 (최소 1개)")
    # 최대 5장 이미지 제한 정책 적용
    image_urls: Optional[List[str]] = Field(default=[], max_length=5, description="첨부 이미지 URL 목록 (최대 5장)")
    is_spoiler: int = Field(default=0, ge=0, le=1, description="스포일러 여부 (0: 일반, 1: 스포일러)")
        
    @field_validator('image_urls')
    @classmethod
    def check_urls(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError("유효한 HTTP/HTTPS URL이어야 합니다.")
        return v

class PostUpdate(BaseModel):
    """게시물 수정 시 전달받는 데이터 (수정할 필드만 선택적 포함 가능)"""
    title: OptionalNotEmptyStr = Field(None, max_length=255, description="수정할 게시물 제목")
    content: OptionalNotEmptyStr = Field(None, description="수정할 게시물 본문")
    movie_ids: Optional[List[int]] = Field(None, min_length=1, description="수정할 공식 영화 ID 목록")
    image_urls: Optional[List[str]] = Field(None, max_length=5, description="수정할 첨부 이미지 URL 목록")
    is_spoiler: Optional[int] = Field(None, ge=0, le=1, description="스포일러 여부 (0: 일반, 1: 스포일러)")

class CommentCreate(BaseModel):
    content: NotEmptyStr = Field(..., max_length=1000, description="댓글 본문")
    parent_id: Optional[int] = Field(default=None, description="대댓글인 경우 부모 댓글의 ID")
    is_spoiler: int = Field(default=0, ge=0, le=1, description="스포일러 여부 (0: 일반, 1: 스포일러)")

class CommentUpdate(BaseModel):
    content: OptionalNotEmptyStr = Field(default=None, max_length=1000, description="수정할 댓글 본문")
    is_spoiler: Optional[int] = Field(default=None, ge=0, le=1, description="스포일러 여부 (0: 일반, 1: 스포일러)")

class LikeToggleRequest(BaseModel):
    target_type: Literal["POST", "COMMENT"] = Field(..., description="POST 또는 COMMENT")
    target_id: int = Field(..., description="대상 게시물/댓글 ID")
