from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.session import engine, get_db
from app.db.base import Base

# DB 테이블 생성 (Alembic 사용 전 빠른 확인용)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="KAKAMU_BE API")

@app.get("/health")
def health_check():
    """쿠버네티스 상태 확인용 엔드포인트"""
    return {"status": "healthy", "version": "1.0.0"}
@app.get("/")
def read_root():
    return {"message": "Welcome to KAKAMU_BE Platform"}

# DB 연결 테스트용 엔드포인트
@app.get("/db-test")
def test_db(db: Session = Depends(get_db)):
    return {"status": "Database connection successful"}