from uuid import UUID

from sqlalchemy.orm import Session

from app.models import User
from app.schemas.request.ml.ingest import (
    MlIngestFeedDeleteEnvelope,
    MlIngestFeedDeletePayload,
    MlIngestFeedEnvelope,
    MlIngestFeedPayload,
)
from app.schemas.request.post import PostCreate, PostUpdate
from app.service.ml import ml_ingest_service
from app.service.ml.sync import safe_ml_call
from app.utils.parser import parse_content


def _resolve_mentioned_user_ids(db: Session, content: str) -> list[str]:
    _, mentions = parse_content(content)
    mentioned_user_ids: list[str] = []
    for mention_str in mentions:
        if "#" not in mention_str:
            continue
        nickname, tag = mention_str.split("#", 1)
        target_user = db.query(User).filter(
            User.nickname == nickname,
            User.tag == tag,
            User.status == "ACTIVE",
        ).first()
        if target_user:
            mentioned_user_ids.append(str(target_user.id))
    return mentioned_user_ids


class PostMlSyncService:
    async def sync_create(
        self,
        db: Session,
        *,
        post_id: int,
        user_id: UUID,
        persona_id: UUID,
        post_in: PostCreate,
    ) -> None:
        movie_ids = [str(movie_id) for movie_id in post_in.movie_ids]
        envelope = MlIngestFeedEnvelope(
            payload=MlIngestFeedPayload(
                feed_id=str(post_id),
                user_id=str(user_id),
                persona_id=str(persona_id),
                content=post_in.content,
                known_movie_ids=movie_ids,
                related_movie_id=movie_ids[0] if movie_ids else None,
                mentioned_user_ids=_resolve_mentioned_user_ids(db, post_in.content),
            )
        )
        await safe_ml_call("ingest feed create", lambda: ml_ingest_service.create_feed(envelope))

    async def sync_update(
        self,
        db: Session,
        *,
        post_id: int,
        user_id: UUID,
        persona_id: UUID,
        post_in: PostUpdate,
    ) -> None:
        movie_ids = [str(movie_id) for movie_id in post_in.movie_ids]
        envelope = MlIngestFeedEnvelope(
            payload=MlIngestFeedPayload(
                feed_id=str(post_id),
                user_id=str(user_id),
                persona_id=str(persona_id),
                content=post_in.content,
                known_movie_ids=movie_ids,
                related_movie_id=movie_ids[0] if movie_ids else None,
                mentioned_user_ids=_resolve_mentioned_user_ids(db, post_in.content),
            )
        )
        await safe_ml_call("ingest feed modify", lambda: ml_ingest_service.modify_feed(envelope))

    async def sync_delete(self, *, post_id: int, user_id: UUID) -> None:
        envelope = MlIngestFeedDeleteEnvelope(
            payload=MlIngestFeedDeletePayload(
                feed_id=str(post_id),
                user_id=str(user_id),
            )
        )
        await safe_ml_call("ingest feed delete", lambda: ml_ingest_service.delete_feed(envelope))


post_ml_sync_service = PostMlSyncService()
