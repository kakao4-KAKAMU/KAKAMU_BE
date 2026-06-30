from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import SaveLog


def get_saved_target_ids(
    db: Session,
    user_id: Optional[UUID],
    target_type: str,
    target_ids: list[int],
) -> set[int]:
    if not user_id or not target_ids:
        return set()

    saved_logs = db.query(SaveLog.target_id).filter(
        SaveLog.user_id == user_id,
        SaveLog.target_type == target_type,
        SaveLog.target_id.in_(target_ids),
        SaveLog.is_active == 1,
    ).all()
    return {log[0] for log in saved_logs}


def is_movie_saved(db: Session, user_id: Optional[UUID], movie_id: UUID) -> bool:
    if not user_id:
        return False

    return db.query(SaveLog).filter(
        SaveLog.user_id == user_id,
        SaveLog.target_type == "MOVIE",
        SaveLog.movie_id == movie_id,
        SaveLog.is_active == 1,
    ).first() is not None
