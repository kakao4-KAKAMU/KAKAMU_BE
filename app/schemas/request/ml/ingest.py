from datetime import datetime

from pydantic import BaseModel, Field

from app.models.ml import JudgeType


class MlIngestMovieJudgePayload(BaseModel):
    movie_id: str = Field(..., min_length=1, description="영화 ID")
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    persona_id: str | None = Field(default=None, description="페르소나 ID")
    judge_type: JudgeType = Field(default=JudgeType.LIKE, description="like/dislike")
    created_at: datetime | None = Field(default=None, description="판정 시각 (ISO 8601)")


class MlIngestMovieJudgeEnvelope(BaseModel):
    payload: MlIngestMovieJudgePayload


class MlIngestPersonJudgePayload(BaseModel):
    person_id: str = Field(..., min_length=1, description="인물 ID")
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    persona_id: str | None = Field(default=None, description="페르소나 ID")
    judge_type: JudgeType = Field(default=JudgeType.LIKE, description="like/dislike")
    created_at: datetime | None = Field(default=None, description="판정 시각 (ISO 8601)")


class MlIngestPersonJudgeEnvelope(BaseModel):
    payload: MlIngestPersonJudgePayload


class MlIngestUserPayload(BaseModel):
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    nickname: str | None = Field(default=None, description="표시 이름")
    created_at: datetime | None = Field(default=None, description="가입 시각 (ISO 8601)")


class MlIngestUserEnvelope(BaseModel):
    payload: MlIngestUserPayload


class MlIngestPersonaPayload(BaseModel):
    persona_id: str = Field(..., min_length=1, description="페르소나 ID")
    user_id: str = Field(..., min_length=1, description="소속 사용자 ID")
    label: str | None = Field(default=None, description="페르소나 표시명")
    genres: list[str] = Field(default_factory=list, description="좋아하는 장르")
    movies: list[str] = Field(default_factory=list, description="관심 영화 ID 목록")
    persons: list[str] = Field(default_factory=list, description="좋아하는 감독/배우 ID 목록")
    created_at: datetime | None = Field(default=None, description="생성 시각 (ISO 8601)")
    modified_at: datetime | None = Field(default=None, description="수정 시각 (ISO 8601)")


class MlIngestPersonaEnvelope(BaseModel):
    payload: MlIngestPersonaPayload


class MlIngestPersonaDeletePayload(BaseModel):
    persona_id: str = Field(..., min_length=1, description="페르소나 ID")
    user_id: str = Field(..., min_length=1, description="사용자 ID")


class MlIngestPersonaDeleteEnvelope(BaseModel):
    payload: MlIngestPersonaDeletePayload


class MlIngestFeedPayload(BaseModel):
    feed_id: str = Field(..., min_length=1, description="피드 ID")
    user_id: str = Field(..., min_length=1, description="작성자 ID")
    content: str = Field(..., min_length=1, description="피드 본문")
    persona_id: str | None = Field(default=None, description="작성 페르소나 ID")
    related_movie_id: str | None = Field(default=None, description="연결된 영화 ID")
    known_movie_ids: list[str] = Field(default_factory=list, description="참조 영화 후보 ID 목록")
    mentioned_user_ids: list[str] = Field(default_factory=list, description="@언급된 사용자 ID")
    created_at: datetime | None = Field(default=None, description="작성 시각 (ISO 8601)")
    modified_at: datetime | None = Field(default=None, description="수정 시각 (ISO 8601)")


class MlIngestFeedEnvelope(BaseModel):
    payload: MlIngestFeedPayload


class MlIngestFeedDeletePayload(BaseModel):
    feed_id: str = Field(..., min_length=1, description="피드 ID")
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    deleted_at: datetime | None = Field(default=None, description="삭제 시각 (ISO 8601)")


class MlIngestFeedDeleteEnvelope(BaseModel):
    payload: MlIngestFeedDeletePayload


class MlIngestFeedLikePayload(BaseModel):
    feed_id: str = Field(..., min_length=1, description="피드 ID")
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    persona_id: str | None = Field(default=None, description="페르소나 ID")
    is_like: bool = Field(default=True, description="True=좋아요, False=취소")
    created_at: datetime | None = Field(default=None, description="반응 시각 (ISO 8601)")


class MlIngestFeedLikeEnvelope(BaseModel):
    payload: MlIngestFeedLikePayload


class MlIngestCommentPayload(BaseModel):
    comment_id: str = Field(..., min_length=1, description="댓글 ID")
    feed_id: str = Field(..., min_length=1, description="피드 ID")
    user_id: str = Field(..., min_length=1, description="작성자 ID")
    content: str = Field(..., min_length=1, description="댓글 본문")
    persona_id: str | None = Field(default=None, description="작성 페르소나 ID")
    mentioned_user_ids: list[str] = Field(default_factory=list, description="@언급된 사용자 ID")
    parent_comment_id: str | None = Field(default=None, description="부모 댓글 ID")
    created_at: datetime | None = Field(default=None, description="작성 시각 (ISO 8601)")
    modified_at: datetime | None = Field(default=None, description="수정 시각 (ISO 8601)")


class MlIngestCommentEnvelope(BaseModel):
    payload: MlIngestCommentPayload


class MlIngestCommentDeletePayload(BaseModel):
    comment_id: str = Field(..., min_length=1, description="댓글 ID")
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    deleted_at: datetime | None = Field(default=None, description="삭제 시각 (ISO 8601)")


class MlIngestCommentDeleteEnvelope(BaseModel):
    payload: MlIngestCommentDeletePayload


class MlIngestCommentLikePayload(BaseModel):
    comment_id: str = Field(..., min_length=1, description="댓글 ID")
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    persona_id: str | None = Field(default=None, description="페르소나 ID")
    is_like: bool = Field(default=True, description="True=좋아요, False=취소")
    created_at: datetime | None = Field(default=None, description="반응 시각 (ISO 8601)")


class MlIngestCommentLikeEnvelope(BaseModel):
    payload: MlIngestCommentLikePayload
