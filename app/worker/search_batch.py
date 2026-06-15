import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from app.db.session import SessionLocal
from app.models.search_log import SearchLog, SearchDailyStat

logger = logging.getLogger(__name__)
def run_daily_search_aggregation():
    """
    [매일 새벽 실행] 전날 데이터 집계 (Roll-up) 및 오래된 원본 데이터 삭제 (Hard Delete)
    """
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        delete_threshold = today - timedelta(days=7) # 7일 지난 데이터

        # 1. 전날(yesterday)의 검색 로그를 Group By 하여 집계
        summary_query = (
            db.query(
                SearchLog.keyword,
                func.count(SearchLog.id).label("search_count")
            )
            .filter(func.date(SearchLog.created_at) == yesterday)
            .group_by(SearchLog.keyword)
            .all()
        )

        # [멱등성 보장] 배치가 중복 실행되더라도 데이터가 꼬이지 않도록 어제 날짜의 기존 통계를 먼저 삭제
        db.query(SearchDailyStat).filter(SearchDailyStat.stat_date == yesterday).delete(synchronize_session=False)

        # 2. 통계 테이블(SearchDailyStat)에 집계 데이터 일괄 저장
        if summary_query:
            stats = [
                SearchDailyStat(
                    stat_date=yesterday,
                    keyword=row.keyword,
                    search_count=row.search_count
                )
                for row in summary_query
            ]
            db.add_all(stats)

        # 3. 7일이 경과한 쓸모없는 Raw 로그는 영구 삭제하여 DB 용량 방어
        deleted_rows = db.query(SearchLog).filter(func.date(SearchLog.created_at) < delete_threshold).delete(synchronize_session=False)

        db.commit()
        logger.info(f"[Batch] 검색어 집계 완료. 집계 키워드: {len(summary_query)}건 / 오래된 로그 삭제: {deleted_rows}건")

    except Exception as e:
        db.rollback()
        logger.error(f"[Batch] 검색어 집계 배치 실패: {e}")
    finally:
        db.close()
