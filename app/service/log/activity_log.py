import logging
from uuid import UUID

from app.models.ml import JudgeType
from app.schemas.request.log import ActivityLogCreate
from app.schemas.request.ml.ingest import (
    MlIngestCommentLikeEnvelope,
    MlIngestCommentLikePayload,
    MlIngestFeedLikeEnvelope,
    MlIngestFeedLikePayload,
    MlIngestMovieJudgeEnvelope,
    MlIngestMovieJudgePayload,
    MlIngestPersonJudgeEnvelope,
    MlIngestPersonJudgePayload,
)
from app.service.ml import ml_ingest_service
from app.service.ml.sync import safe_ml_call

logger = logging.getLogger(__name__)


class ActivityLogService:
    async def process_activity_log(
        self,
        user_id: UUID,
        persona_id: UUID,
        log_data: ActivityLogCreate,
    ) -> None:
        target_type = log_data.target_type.upper()
        action = log_data.action.lower()
        target_id = str(log_data.target_id)

        if target_type == "MOVIE" and action in {"like", "dislike"}:
            envelope = MlIngestMovieJudgeEnvelope(
                payload=MlIngestMovieJudgePayload(
                    movie_id=target_id,
                    user_id=str(user_id),
                    persona_id=str(persona_id),
                    judge_type=JudgeType.LIKE if action == "like" else JudgeType.DISLIKE,
                )
            )
            await safe_ml_call("ingest movie judge", lambda: ml_ingest_service.judge_movie(envelope))
            return

        if target_type == "PEOPLE" and action in {"like", "dislike"}:
            envelope = MlIngestPersonJudgeEnvelope(
                payload=MlIngestPersonJudgePayload(
                    person_id=target_id,
                    user_id=str(user_id),
                    persona_id=str(persona_id),
                    judge_type=JudgeType.LIKE if action == "like" else JudgeType.DISLIKE,
                )
            )
            await safe_ml_call("ingest person judge", lambda: ml_ingest_service.judge_person(envelope))
            return

        if target_type == "POST" and action in {"like", "unlike", "dislike"}:
            envelope = MlIngestFeedLikeEnvelope(
                payload=MlIngestFeedLikePayload(
                    feed_id=target_id,
                    user_id=str(user_id),
                    persona_id=str(persona_id),
                    is_like=action == "like",
                )
            )
            await safe_ml_call("ingest feed like", lambda: ml_ingest_service.like_feed(envelope))
            return

        if target_type == "COMMENT" and action in {"like", "unlike", "dislike"}:
            envelope = MlIngestCommentLikeEnvelope(
                payload=MlIngestCommentLikePayload(
                    comment_id=target_id,
                    user_id=str(user_id),
                    persona_id=str(persona_id),
                    is_like=action == "like",
                )
            )
            await safe_ml_call("ingest comment like", lambda: ml_ingest_service.like_comment(envelope))
            return

        logger.debug(
            "[ActivityLog] ML ingest 대상이 아닌 로그입니다. target_type=%s action=%s",
            target_type,
            action,
        )


activity_log_service = ActivityLogService()
