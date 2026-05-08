from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.redis import redis_client

router = APIRouter()

@router.get("/health")
def health_check():
    """쿠버네티스 상태 확인용 엔드포인트"""
    return {"status": "healthy", "version": "1.0.0"}

@router.get("/")
def read_root():
    return {"message": "Welcome to KAKAMU_BE Platform"}

# DB 연결 테스트용 엔드포인트
@router.get("/db-test")
def test_db(db: Session = Depends(get_db)):
    return {"status": "Database connection successful"}

@router.get("/redis-test")
async def test_redis():
    try:
        # 이미 상단에서 가져온 redis_client 사용
        await redis_client.set("test_key", "Hello Redis!", ex=60) # 60초 후 만료 예시
        value = await redis_client.get("test_key")
        return {"status": "success", "value": value}
    except Exception as e:
        return {"status": "error", "message": str(e)}
