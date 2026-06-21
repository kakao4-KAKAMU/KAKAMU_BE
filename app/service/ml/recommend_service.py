from app.schemas.request.ml.recommend import MlRecommendRequest
from app.schemas.response.ml.recommend import MlFeedRecommendResponse, MlMovieRecommendResponse
from app.service.ml.client import MlApiClient, ml_api_client


class MlRecommendService:
    def __init__(self, client: MlApiClient | None = None):
        self._client = client or ml_api_client

    async def recommend_movie(self, request: MlRecommendRequest) -> MlMovieRecommendResponse:
        response = await self._client.post(
            "/recommend/movie",
            json=request.model_dump(mode="json", exclude_none=True),
        )
        return MlMovieRecommendResponse.model_validate(response.json())

    async def recommend_feed(self, request: MlRecommendRequest) -> MlFeedRecommendResponse:
        response = await self._client.post(
            "/recommend/feed",
            json=request.model_dump(mode="json", exclude_none=True),
        )
        return MlFeedRecommendResponse.model_validate(response.json())


ml_recommend_service = MlRecommendService()
