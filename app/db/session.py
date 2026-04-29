from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 환경 변수나 설정 파일에서 DB URL을 가져옵니다.
# 예: postgresql://admin:password@localhost:5432/main_db
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/main_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI Dependency로 사용할 세션 생성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()