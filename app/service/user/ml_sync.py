from uuid import UUID

from app.schemas.request.ml.ingest import MlIngestUserEnvelope, MlIngestUserPayload
from app.service.ml import ml_ingest_service
from app.service.ml.sync import safe_ml_call


class UserMlSyncService:
    async def sync_user_regist(self, user_id: UUID, nickname: str | None = None) -> None:
        envelope = MlIngestUserEnvelope(
            payload=MlIngestUserPayload(
                user_id=str(user_id),
                nickname=nickname,
            )
        )
        await safe_ml_call("ingest user regist", lambda: ml_ingest_service.regist_user(envelope))


user_ml_sync_service = UserMlSyncService()
