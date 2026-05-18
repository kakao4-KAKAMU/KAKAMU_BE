from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

from app.core.config import settings
from app.core.redis import redis_client
from app.api.api import api_router

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
        
    yield
    
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
    # allow_credentials=True 일 때는 명시적인 도메인을 지정해야 합니다. (보안 정책)
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE 등 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# 중앙 라우터 허브 등록
app.include_router(api_router)
