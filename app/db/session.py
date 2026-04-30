from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 운영 환경을 위한 커넥션 풀 설정
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,           # 동시 연결 수 상향
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True      # 연결 유효성 체크
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()