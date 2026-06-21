from app.schemas.request.ml.ingest import (
    MlIngestCommentDeleteEnvelope,
    MlIngestCommentEnvelope,
    MlIngestCommentLikeEnvelope,
    MlIngestFeedDeleteEnvelope,
    MlIngestFeedEnvelope,
    MlIngestFeedLikeEnvelope,
    MlIngestMovieJudgeEnvelope,
    MlIngestPersonJudgeEnvelope,
    MlIngestPersonaDeleteEnvelope,
    MlIngestPersonaEnvelope,
    MlIngestUserEnvelope,
)
from app.schemas.response.ml.ingest import MlIngestResponse
from app.service.ml.client import MlApiClient, ml_api_client


class MlIngestService:
    def __init__(self, client: MlApiClient | None = None):
        self._client = client or ml_api_client

    async def _post_ingest(self, path: str, envelope) -> MlIngestResponse:
        response = await self._client.post(
            path,
            json=envelope.model_dump(mode="json", exclude_none=True),
        )
        return MlIngestResponse.model_validate(response.json())

    async def judge_movie(self, envelope: MlIngestMovieJudgeEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/movie/judge", envelope)

    async def judge_person(self, envelope: MlIngestPersonJudgeEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/person/judge", envelope)

    async def regist_user(self, envelope: MlIngestUserEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/user/regist", envelope)

    async def create_persona(self, envelope: MlIngestPersonaEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/persona/create", envelope)

    async def modify_persona(self, envelope: MlIngestPersonaEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/persona/modify", envelope)

    async def delete_persona(self, envelope: MlIngestPersonaDeleteEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/persona/delete", envelope)

    async def create_feed(self, envelope: MlIngestFeedEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/feed/create", envelope)

    async def modify_feed(self, envelope: MlIngestFeedEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/feed/modify", envelope)

    async def delete_feed(self, envelope: MlIngestFeedDeleteEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/feed/delete", envelope)

    async def like_feed(self, envelope: MlIngestFeedLikeEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/feed/like", envelope)

    async def create_comment(self, envelope: MlIngestCommentEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/comment/create", envelope)

    async def modify_comment(self, envelope: MlIngestCommentEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/comment/modify", envelope)

    async def delete_comment(self, envelope: MlIngestCommentDeleteEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/comment/delete", envelope)

    async def like_comment(self, envelope: MlIngestCommentLikeEnvelope) -> MlIngestResponse:
        return await self._post_ingest("/ingest/comment/like", envelope)


ml_ingest_service = MlIngestService()
