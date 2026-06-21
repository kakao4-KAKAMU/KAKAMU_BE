from uuid import UUID

from sqlalchemy.orm import Session

from app.models import User
from app.schemas.request.ml.ingest import (
    MlIngestCommentDeleteEnvelope,
    MlIngestCommentDeletePayload,
    MlIngestCommentEnvelope,
    MlIngestCommentPayload,
)
from app.schemas.request.post import CommentCreate, CommentUpdate
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


class CommentMlSyncService:
    async def sync_create(
        self,
        db: Session,
        *,
        comment_id: int,
        post_id: int,
        user_id: UUID,
        persona_id: UUID,
        comment_in: CommentCreate,
    ) -> None:
        envelope = MlIngestCommentEnvelope(
            payload=MlIngestCommentPayload(
                comment_id=str(comment_id),
                feed_id=str(post_id),
                user_id=str(user_id),
                persona_id=str(persona_id),
                content=comment_in.content,
                parent_comment_id=str(comment_in.parent_id) if comment_in.parent_id else None,
                mentioned_user_ids=_resolve_mentioned_user_ids(db, comment_in.content),
            )
        )
        await safe_ml_call("ingest comment create", lambda: ml_ingest_service.create_comment(envelope))

    async def sync_update(
        self,
        db: Session,
        *,
        comment_id: int,
        post_id: int,
        user_id: UUID,
        persona_id: UUID | None,
        comment_in: CommentUpdate,
    ) -> None:
        if comment_in.content is None:
            return

        envelope = MlIngestCommentEnvelope(
            payload=MlIngestCommentPayload(
                comment_id=str(comment_id),
                feed_id=str(post_id),
                user_id=str(user_id),
                persona_id=str(persona_id) if persona_id else None,
                content=comment_in.content,
                mentioned_user_ids=_resolve_mentioned_user_ids(db, comment_in.content),
            )
        )
        await safe_ml_call("ingest comment modify", lambda: ml_ingest_service.modify_comment(envelope))

    async def sync_delete(self, *, comment_id: int, user_id: UUID) -> None:
        envelope = MlIngestCommentDeleteEnvelope(
            payload=MlIngestCommentDeletePayload(
                comment_id=str(comment_id),
                user_id=str(user_id),
            )
        )
        await safe_ml_call("ingest comment delete", lambda: ml_ingest_service.delete_comment(envelope))


comment_ml_sync_service = CommentMlSyncService()
