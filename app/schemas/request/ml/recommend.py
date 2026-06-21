from pydantic import BaseModel, Field


class MlRecommendRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="사용자 ID")
    query: str = Field(..., min_length=1, description="추천 쿼리")
    persona_id: str | None = Field(default=None, description="페르소나 ID")
    top_k: int = Field(default=10, ge=1, le=50, description="추천 결과 상위 K")
    vec_top_k: int = Field(default=30, ge=1, le=100, description="벡터 검색 상위 K")
    max_toxicity: float = Field(default=0.7, ge=0.0, le=1.0, description="최대 독성 점수")
