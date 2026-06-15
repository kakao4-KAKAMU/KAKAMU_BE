from sqlalchemy import Column, Integer, String, DateTime, Date, func, UniqueConstraint
from app.db.base import Base

class SearchLog(Base):
    """유저의 원본 검색 기록을 저장하는 Raw Log 테이블"""
    __tablename__ = "search_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), index=True, nullable=True) # 로그인하지 않은 유저도 고려하여 Nullable
    keyword = Column(String(100), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class SearchDailyStat(Base):
    """매일 새벽 배치를 통해 집계되는 일별 검색어 통계 테이블"""
    __tablename__ = "search_daily_stat"
    
    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, index=True, nullable=False)
    keyword = Column(String(100), index=True, nullable=False)
    search_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint('stat_date', 'keyword', name='uq_search_stat_date_keyword'),
    )