import logging
from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal
from app.models import Persona, Post, Comment

logger = logging.getLogger(__name__)

def hard_delete_old_personas():
    """
    [매일 실행] 삭제(Soft Delete)된 지 7일이 지난 페르소나 영구 삭제 (Hard Delete)
    """
    db = SessionLocal()
    try:
        # 7일 전 기준 시간 계산 (UTC 기준)
        delete_threshold = datetime.now(timezone.utc) - timedelta(days=7)

        # 삭제 대상 페르소나 ID 조회
        target_personas = db.query(Persona.id).filter(
            Persona.status == "DELETED",
            Persona.deleted_at <= delete_threshold
        ).all()

        if not target_personas:
            logger.debug("[Batch] 7일 경과 영구 삭제 대상 페르소나 없음")
            return

        persona_ids = [p_id for (p_id,) in target_personas]

        # 1. 해당 페르소나가 작성한 게시물 및 댓글 비활성화 (INACTIVE)
        updated_posts = db.query(Post).filter(Post.persona_id.in_(persona_ids)).update({"status": "INACTIVE"}, synchronize_session=False)
        updated_comments = db.query(Comment).filter(Comment.persona_id.in_(persona_ids)).update({"status": "INACTIVE"}, synchronize_session=False)

        # 2. 페르소나 영구 삭제 (Hard Delete)
        deleted_rows = db.query(Persona).filter(Persona.id.in_(persona_ids)).delete(synchronize_session=False)

        db.commit()
        logger.info(f"[Batch] 7일 경과 페르소나 영구 삭제 완료: {deleted_rows}건 (비활성화된 게시물: {updated_posts}건, 댓글: {updated_comments}건)")

    except Exception as e:
        db.rollback()
        logger.error(f"[Batch] 페르소나 영구 삭제 배치 실패: {e}")
    finally:
        db.close()
