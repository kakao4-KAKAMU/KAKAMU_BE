import logging
from app.db.session import SessionLocal
from app.service.notification.notification_service import notification_service

logger = logging.getLogger(__name__)

def clean_expired_notifications_task():
    """
    정책 4: 매일 특정 시간에 실행되어 생성 후 30일이 지난 알림을 영구 삭제합니다.
    app/worker/scheduler.py 내의 APScheduler에 등록해야 합니다.
    """
    db = SessionLocal()
    try:
        notification_service.delete_expired_notifications(db)
        logger.info("[Cron] 30일 경과 만료 알림 삭제 작업 완료")
    except Exception as e:
        logger.error(f"[Cron] 만료 알림 삭제 실패: {e}")
        db.rollback()
    finally:
        db.close()