import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config

from app.db.session import engine, get_db
from app.db.base import Base
from app.models import models
from app.core.config import settings
from app.core.redis import redis_client
from app.service.recommendation import recommendation_service
from app.service.persona import persona_service

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
    
    try:
        await redis_client.ping()
        print("Successfully connected to Redis!")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        
    yield
    
    await redis_client.close()
    
    # 앱 종료 시 실행될 로직 (Shutdown)이 필요하다면 여기에 작성
    print("Shutting down...")

async def get_current_persona(x_user_id: int = Header(...)):
    """
    헤더에서 user_id를 받아 현재 활성화된 페르소나 ID를 반환하는 공통 의존성
    """
    persona_id = await persona_service.get_active_persona_id(x_user_id)
    if not persona_id:
        raise HTTPException(status_code=400, detail="활성화된 페르소나가 없습니다. 페르소나를 선택해주세요.")
    return persona_id

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

@app.get("/redis-test")
async def test_redis():
    try:
        # 이미 상단에서 가져온 redis_client 사용
        await redis_client.set("test_key", "Hello Redis!", ex=60) # 60초 후 만료 예시
        value = await redis_client.get("test_key")
        return {"status": "success", "value": value}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/movies/{movie_id}/watch")
async def watch_movie(movie_id: int, user_id: int):
    # 1. 현재 어떤 페르소나로 접속 중인지 Redis에서 조회
    persona_id = await persona_service.get_active_persona_id(user_id)
    if not persona_id:
        return {"error": "페르소나를 먼저 선택하세요."}

    # 2. 활동 기록 및 취향 반영 (장르는 DB에서 가져왔다고 가정)
    await recommendation_service.record_activity(persona_id, movie_id, "view")
    await recommendation_service.update_persona_preference(persona_id, ["Action", "Sci-Fi"])
    
    return {"message": f"Persona {persona_id} watched movie {movie_id}"}

@app.get("/movies/recommend")
async def get_movies(active_persona_id: int = Depends(get_current_persona)):
    # 1. 이제 active_persona_id를 바로 사용 가능!
    # 2. 이 ID로 RecommendationService의 context를 불러옴
    context = await recommendation_service.get_recent_persona_context(active_persona_id)
    return {"recommendations": "...", "for_persona": active_persona_id}








### 테스트용 코드
@app.post("/test/activity")
async def test_record_activity(movie_id: int, genres: str, persona_id: int):
    """페르소나 활동 기록 테스트 (genres는 'Action,Sci-Fi' 형태)"""
    genre_list = [g.strip() for g in genres.split(",")]
    await recommendation_service.record_activity(persona_id, movie_id, "view")
    await recommendation_service.update_persona_preference(persona_id, genre_list)
    return {"message": "활동 기록 완료"}

@app.get("/test/context/{persona_id}")
async def test_get_context(persona_id: int):
    """페르소나의 실시간 컨텍스트 조회 테스트"""
    context = await recommendation_service.get_persona_context(persona_id)
    return context