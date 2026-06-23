from datetime import datetime
from uuid import UUID

from app.models.ml import JudgeType
from app.schemas.request.ml.ingest import MlIngestMovieJudgeEnvelope, MlIngestMovieJudgePayload
from app.service.ml import ml_ingest_service
from app.service.ml.sync import safe_ml_call


class MovieEvaluationMlSyncService:
    async def sync_movie_judge(
        self,
        *,
        movie_id: UUID,
        user_id: UUID,
        persona_id: UUID | None,
        evaluation: str,
        created_at: datetime | None = None,
    ) -> None:
        judge_type = JudgeType.LIKE if evaluation == "LIKE" else JudgeType.DISLIKE
        envelope = MlIngestMovieJudgeEnvelope(
            payload=MlIngestMovieJudgePayload(
                movie_id=str(movie_id),
                user_id=str(user_id),
                persona_id=str(persona_id) if persona_id else None,
                judge_type=judge_type,
                created_at=created_at or datetime.utcnow(),
            )
        )
        await safe_ml_call(
            "ingest movie judge",
            lambda: ml_ingest_service.judge_movie(envelope),
        )


movie_evaluation_ml_sync_service = MovieEvaluationMlSyncService()
