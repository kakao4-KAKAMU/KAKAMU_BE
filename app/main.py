import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config

from app.db.session import engine, get_db
from app.db.base import Base
from app.models import models
from app.core.config import settings

def run_migrations():
    """애플리케이션 시작 시 Alembic 마이그레이션을 자동으로 실행합니다."""
    # 1. alembic.ini 경로 설정 (프로젝트 루트 기준)
    alembic_cfg = Config("alembic.ini")
    
    # 2. 실시간으로 환경 변수의 DB URL을 Alembic 설정에 주입
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    # 3. 'alembic upgrade head' 명령어 실행
    try:
        print("Running DB migrations...")
        command.upgrade(alembic_cfg, "head")
        print("Migrations complete!")
    except Exception as e:
        print(f"Migration failed: {e}")

# --- 앱 시작 시 자동으로 마이그레이션 실행 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시 실행될 로직 (Startup)
    run_migrations()
    yield
    # 앱 종료 시 실행될 로직 (Shutdown)이 필요하다면 여기에 작성
    print("Shutting down...")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

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