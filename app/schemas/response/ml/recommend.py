from pydantic import BaseModel, Field

from app.schemas.base.movie import Movie

class MlMovieRecommendItem(BaseModel):
    movie_id: str = Field(..., description="영화 ID")
    title: str = Field(..., description="영화 제목")
    plot_summary: str = Field(..., description="영화 줄거리")
    score: float = Field(..., description="영화 추천 점수")


class MlMovieRecommendResponse(BaseModel):
    arm_id: str = Field(..., description="ARM ID")
    movies: list[MlMovieRecommendItem] = Field(..., description="영화 목록")
    keywords: list[str] = Field(..., description="키워드 목록")
    themes: list[str] = Field(..., description="테마 목록")
    moods: list[str] = Field(..., description="무드 목록")


class MovieRecommendResponse(BaseModel):
    arm_id: str = Field(..., description="ARM ID")
    movies: list[Movie] = Field(..., description="영화 목록")
    keywords: list[str] = Field(..., description="키워드 목록")
    themes: list[str] = Field(..., description="테마 목록")
    moods: list[str] = Field(..., description="무드 목록")


class MlFeedRecommendItem(BaseModel):
    feed_id: str = Field(..., description="피드 ID")
    summary: str = Field(..., description="피드 요약")
    sentiment_score: float = Field(..., description="피드 감정 점수")
    score: float = Field(..., description="피드 추천 점수")


class MlFeedRecommendResponse(BaseModel):
    arm_id: str = Field(..., description="ARM ID")
    feeds: list[MlFeedRecommendItem] = Field(..., description="피드 목록")
    keywords: list[str] = Field(..., description="키워드 목록")
    themes: list[str] = Field(..., description="테마 목록")
    moods: list[str] = Field(..., description="무드 목록")
