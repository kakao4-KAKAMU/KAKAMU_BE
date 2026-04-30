from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

import os
import time

# 운영 환경을 위한 커넥션 풀 설정
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,           # 동시 연결 수 상향
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True      # 연결 유효성 체크
)

# 환경 변수에서 URL을 가져오되, 기본값은 로컬/K8s 서비스 이름에 맞춥니다.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/main_db")

# 연결 시도 중 에러가 날 수 있으므로 엔진 생성을 신중히 합니다.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True  # 연결이 끊겼는지 미리 확인하는 옵션
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()