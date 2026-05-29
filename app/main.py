import os
import sys
import subprocess

def install_requirements():
    """서버 실행 시 requirements.txt의 패키지를 자동 설치합니다."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        req_path = os.path.join(base_dir, "requirements.txt")
        
        if os.path.exists(req_path):
            print("Checking and installing packages from requirements.txt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", req_path])
    except Exception as e:
        print(f"Failed to install requirements: {e}")

# 3rd-party 모듈들을 임포트하기 전에 설치를 우선 진행합니다.
install_requirements()

from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

from apscheduler.schedulers.background import BackgroundScheduler
from app.core.tracing import setup_tracing
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.redis import redis_client
from app.api.api import api_router
from app.service.sync_task import stat_sync_worker, ml_log_sync_worker
from app.worker.search_batch import run_daily_search_aggregation
from app.db.session import engine

from app.middleware.logging_middleware import LoggingMiddleware

def create_database_if_not_exists():
    """데이터베이스가 존재하지 않으면 생성합니다."""
    db_url = settings.DATABASE_URL
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip('/')
    
    # postgres 데이터베이스에 연결하여 데이터베이스 생성
    postgres_url = db_url.replace(f"/{db_name}", "/postgres")
    
    try:
        # CREATE DATABASE는 트랜잭션 내에서 실행할 수 없으므로 AUTOCOMMIT 모드 적용
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if not result.fetchone():
                print(f"Creating database {db_name}...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database {db_name} created!")
            else:
                print(f"Database {db_name} already exists.")
    except Exception as e:
        print(f"Failed to create database: {e}")

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
    create_database_if_not_exists()
    run_migrations()
    
    try:
        await redis_client.ping()
        print("Successfully connected to Redis!")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        
    # 백그라운드 워커 실행 (Redis -> DB 주기적 동기화 시작)
    sync_task = asyncio.create_task(stat_sync_worker())
    ml_log_task = asyncio.create_task(ml_log_sync_worker())

    # 매일 새벽 3시에 검색어 일일 통계 배치 실행
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_daily_search_aggregation, 'cron', hour=3, minute=0)
    scheduler.start()

    yield
    
    sync_task.cancel() # 서버 종료 시 워커 중지
    ml_log_task.cancel()
    scheduler.shutdown()
    await redis_client.close()
    
    # 앱 종료 시 실행될 로직 (Shutdown)이 필요하다면 여기에 작성
    print("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FILMA 백엔드 API 문서",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path="/api",
    lifespan=lifespan,
)

# --- CORS 설정 ---
# 프론트엔드 웹 브라우저에서 백엔드 API를 호출할 수 있도록 접근을 허용합니다.
app.add_middleware(
    CORSMiddleware,
    # 모든 도메인을 허용합니다. (주의: allow_credentials=True와 함께 사용할 수 없습니다)
    # prod 브랜치에서는 수정 필요(특정 도메인만 허용)
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],  # GET, POST, PUT, DELETE 등 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)
setup_tracing(app)
# 로그 미들웨어 등록
app.add_middleware(LoggingMiddleware)

# 중앙 라우터 허브 등록
app.include_router(api_router)

# static 폴더 서빙 추가

app.mount("/static", StaticFiles(directory="app/static"), name="static")
