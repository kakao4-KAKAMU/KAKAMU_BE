from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.session import engine, get_db
from app.db.base import Base

# DB 테이블 생성 (Alembic 사용 전 빠른 확인용)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie SNS API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Movie SNS Platform"}

# DB 연결 테스트용 엔드포인트
@app.get("/db-test")
def test_db(db: Session = Depends(get_db)):
    return {"status": "Database connection successful"}