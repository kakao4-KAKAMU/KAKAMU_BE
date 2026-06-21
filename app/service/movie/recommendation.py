from uuid import UUID

from app.schemas.request.ml.recommend import MlRecommendRequest
from app.schemas.response.ml.recommend import MlMovieRecommendResponse
from app.service.ml import ml_recommend_service


class MovieRecommendationService:
    async def recommend(
        self,
        user_id: UUID,
        persona_id: UUID,
        query: str = "맞춤 영화 추천",
    ) -> MlMovieRecommendResponse:
        return await ml_recommend_service.recommend_movie(
            MlRecommendRequest(
                user_id=str(user_id),
                persona_id=str(persona_id),
                query=query,
            )
        )


movie_recommendation_service = MovieRecommendationService()
